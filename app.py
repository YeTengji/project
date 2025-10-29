import os
import logging
import pytz

from datetime import datetime, time, timedelta, timezone
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, login_user, logout_user, current_user

from sqlalchemy import select, or_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload

from context import inject_calendar_share_status_enums, inject_theme_from_cookie, inject_user_profile_form
from extensions import csrf, db, login_manager, mail
from forms import AddEventForm, ChangePasswordForm, EditEventForm, ForgotPasswordForm, LoginForm, ResetPasswordForm, ShareCalendarRequestForm, ShareCalendarResponseForm, SignUpForm, UserProfileForm, VerifyPasswordResetCodeForm
from helpers import database_to_calendarview, generate_secure_code, get_or_create_calendar_image, inspire, send_reset_code_email, render_week_schedule, update_calendar_image
from models import CalendarEvent, CalendarEventDay, CalendarImage, CalendarShare, CalendarShareStatus, NotepadData, PreviousPassword, ResetCode, User, UserTheme

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['APP_NAME'] = 'I.G.K.H.'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    # Email Information
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = "Please sign in to continue."
    login_manager.login_message_category = "warning"
    db.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    '''
    if code generates multiple context processors, use the following loop
    for processor in [processor1, processor2, processor3]:
        app.context_processor(processor)
    '''
    for processor in [inject_calendar_share_status_enums, inject_theme_from_cookie, inject_user_profile_form]:
        app.context_processor(processor)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def root():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

#region --- Authentication and Registration Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    login_form = LoginForm()
    signup_form = SignUpForm()

    forms = {
        'login_form': login_form,
        'signup_form': signup_form,
    }

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'login' and login_form.validate_on_submit():
            identifier = login_form.identifier.data.strip()

            stmt = select(User).where(or_(User.username == identifier, func.lower(User.email) == identifier.lower()))
            user = db.session.execute(stmt).scalar_one_or_none()
            if user and check_password_hash(user.password, login_form.password.data):
                login_user(user, remember=login_form.remember.data)
                user.theme.theme = login_form.theme.data
                db.session.commit()
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials.', 'danger')
                return redirect(url_for('login'))
        
        elif form_type =='signup' and signup_form.validate_on_submit():
            existing_email = db.session.execute(select(User).where(func.lower(User.email) == signup_form.email.data.lower())).scalar_one_or_none()
            if existing_email:
                flash('Email already registered. Please log in.', 'danger')
                return redirect(url_for('login'))
            
            new_user = User(
                first_name=signup_form.first_name.data.strip(),
                last_name=signup_form.last_name.data.strip(),
                username=signup_form.username.data,
                email=signup_form.email.data.strip().lower(),
                password=generate_password_hash(signup_form.password.data),
                country=signup_form.country.data,
                time_zone=signup_form.time_zone.data
            )

            user_theme = UserTheme(theme=signup_form.theme.data)
            new_user.theme = user_theme

            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Account created successfully. Please log in.', 'success')
            except SQLAlchemyError as e:
                db.session.rollback()
                logging.error(f"Sign up database error: {e}")
                flash('Something went wrong. Please contact support.', 'danger')
                return redirect(url_for('login'))
            
            return redirect(url_for('login'))
        
    return render_template('login.html', **forms)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    forgot_password_form = ForgotPasswordForm()

    if request.method == 'POST':
        if forgot_password_form.validate_on_submit():
            existing_email = db.session.execute(select(User).where(
                func.lower(User.email) == forgot_password_form.email.data.lower()
                )
            ).scalar_one_or_none()

            if existing_email:
                now = datetime.now(timezone.utc)
                validity = timedelta(minutes=15)

                recent_code = db.session.execute(select(ResetCode).where(
                    ResetCode.user_id == existing_email.id,
                    ResetCode.requested > now - validity,
                    ResetCode.used.is_(False)
                    )
                ).scalar_one_or_none()

                if recent_code:
                    flash('A code was sent previously. Please check your email messages', 'warning')
                    return redirect(url_for('forgot_password'))

                reset_code = ResetCode(
                    user_id = existing_email.id,
                    code=generate_secure_code(),
                    requested=now,
                    expiration=now + validity
                )

                try:
                    db.session.add(reset_code)
                    db.session.commit()
                    send_reset_code_email(existing_email.email, reset_code.code)
                except SQLAlchemyError as e:
                    logging.error(f"Reset code database error: {e}")
                    flash('Something went wrong. Please contact support.', 'danger')
                    return redirect(url_for('forgot_password'))

            flash('Please check your email for further instructions.', 'info')
            return redirect(url_for('verify_password_reset_code'))
                
    return render_template('forgot_password.html', forgot_password_form=forgot_password_form)

@app.route('/verify-password-reset-code', methods=['GET', 'POST'])
def verify_password_reset_code():
    verify_password_reset_code_form = VerifyPasswordResetCodeForm()

    if request.method == 'POST':
        if verify_password_reset_code_form.validate_on_submit():
            code = db.session.execute(select(ResetCode).where(
                ResetCode.code == verify_password_reset_code_form.code.data
                )
            ).scalar_one_or_none()

            if code and code.expiration > datetime.now(timezone.utc):
                session['code_verified_user_id'] = code.user_id
                code.used = True
                db.session.commit()
                return redirect(url_for('reset_password'))
            else:
                flash('Invalid code.', 'danger')
                return redirect(url_for('verify_password_reset_code'))
            
    return render_template('verify_password_reset_code.html', verify_password_reset_code_form=verify_password_reset_code_form)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    user_id = session.get('code_verified_user_id')
    if not user_id:
        session.pop('code_verified_user_id', None)
        flash('Unauthorized.', 'danger')
        return redirect(url_for('login'))

    reset_password_form = ResetPasswordForm()

    if request.method == 'POST':
        if reset_password_form.validate_on_submit():
            user = db.session.get(User, user_id)

            if user.has_used_password(reset_password_form.password.data) or check_password_hash (user.password, reset_password_form.password.data):
                flash('Please create a different password.', 'danger')
                return render_template('reset_password.html', reset_password_form=reset_password_form)

            db.session.add(PreviousPassword(
                user_id=user.id,
                previous_password=user.password,
                change_date=datetime.now(timezone.utc)
            ))
            user.password = generate_password_hash(reset_password_form.password.data)
            db.session.commit()
            db.session.refresh(user)
            if len(user.previous_passwords) > 5:
                for p in sorted(user.previous_passwords, key=lambda p: p.change_date)[:-5]:
                    db.session.delete(p)
            db.session.commit()

            session.pop('code_verified_user_id', None)

            flash('Password reset successful. Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('reset_password.html', reset_password_form=reset_password_form)

@app.route('/get-time-zones', methods=['POST'])
def get_time_zones():
    data = request.get_json(force=True)
    country_code = data.get('country', '').strip().upper()
    if len(country_code) != 2:
        return jsonify({'time_zones': [], 'readonly': False}), 400
    time_zones = pytz.country_timezones.get(country_code.upper(), [])
    return jsonify({
        'time_zones': time_zones,
        'readonly': len(time_zones) == 1
    })

#endregion --------

#region --- User Admin Routes ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout Successful.', 'info')

    return redirect(url_for('login'))

@app.route('/user-profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    user_profile_form = UserProfileForm()

    if user_profile_form.validate_on_submit():

        unchanged = (
            user_profile_form.first_name.data == current_user.first_name and
            user_profile_form.last_name.data == current_user.last_name and
            user_profile_form.username.data == current_user.username and
            user_profile_form.email.data == current_user.email and
            user_profile_form.country.data == current_user.country and
            user_profile_form.time_zone.data == current_user.time_zone
        )

        if unchanged:
            flash("No changes detected.", "info")
            return redirect(url_for('dashboard'))

        current_user.first_name = user_profile_form.first_name.data
        current_user.last_name = user_profile_form.last_name.data
        current_user.username = user_profile_form.username.data
        current_user.email = user_profile_form.email.data
        current_user.country = user_profile_form.country.data
        current_user.time_zone = user_profile_form.time_zone.data
        db.session.commit()

        flash("Profile updated!", "success")
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard.html.jinja', user_profile_form=user_profile_form, show_user_profile_modal=True)

@app.route('/update-theme', methods=['POST'])
@login_required
def update_theme():
    data = request.get_json()
    new_theme = data.get('theme')

    if new_theme not in ['light', 'dark']:
        return jsonify({'error': 'Invalid theme'}), 400
    
    user_theme = db.session.execute(select(UserTheme).where(UserTheme.user_id == current_user.id)).scalar_one_or_none()
    if user_theme:
        user_theme.theme = new_theme
    else:
        user_theme = UserTheme(user_id=current_user.id, theme=new_theme)
        db.session.add(user_theme)

    try:
        db.session.commit()
        return jsonify({'message': 'Theme updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    change_password_form = ChangePasswordForm()

    if change_password_form.validate_on_submit():
        user = current_user
        if not check_password_hash(user.password, change_password_form.current_password.data):
            flash('Incorrect current password.', 'danger')
            return render_template('change_password.html', change_password_form=change_password_form)

        if user.has_used_password(change_password_form.password.data) or check_password_hash (user.password, change_password_form.password.data):
            flash('Please choose a different password.', 'danger')
            change_password_form.password.data = ''
            change_password_form.confirm_password.data = ''
            return render_template('change_password.html', change_password_form=change_password_form)
        
        db.session.add(PreviousPassword(
            user_id=user.id,
            previous_password=user.password,
            change_date=datetime.now(timezone.utc)
        ))

        user.password = generate_password_hash(change_password_form.password.data)
        db.session.commit()
        db.session.refresh(user)
        if len(user.previous_passwords) > 5:
            for p in sorted(user.previous_passwords, key=lambda p: p.change_date)[:-5]:
                db.session.delete(p)
        db.session.commit()

        flash('Password changed successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html', change_password_form=change_password_form)
#endregion

#region --- Dashbaord Routes ---
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.time()
    current_date = now.date()
    current_day_of_week = now.weekday()

    if session.get("quote_date") != today:
        quote_data = inspire()
        session["quote"] = quote_data
        session["quote_date"] = today

    inspiration = session.get("quote")
    quote = {
        "text": inspiration[0]["q"],
        "author": inspiration[0]["a"]
    }

    notepad = db.session.execute(
        select(NotepadData)
        .filter(NotepadData.user_id == current_user.id)
    ).scalars().first()

    if not notepad:
        notepad = NotepadData(title='To-Do List', body=[])

    curent_events = (
        db.session.execute(
            select(CalendarEvent)
            .filter(CalendarEvent.user_id == current_user.id,
                or_(
                    CalendarEvent.day == current_date,
                    CalendarEvent.recurring_days.any(CalendarEventDay.day_of_week == current_day_of_week)
                )
            ).order_by(CalendarEvent.start)
        ).scalars().all()
    )

    share_request = db.session.execute(
            select(CalendarShare)
            .filter(CalendarShare.viewer_id == current_user.id)
            .filter(CalendarShare.status == CalendarShareStatus.PENDING)
        ).scalars().first()

    return render_template('dashboard.html.jinja', current_events=curent_events, share_request=share_request, current_time=current_time, current_date=current_date, notepad=notepad, quote=quote)

@app.route('/api/notes', methods=['POST'])
@login_required
def save_note():
    data = request.get_json()
    note = db.session.execute(
        select(NotepadData)
        .filter(NotepadData.user_id == current_user.id)
    ).scalars().first()

    if note:
        note.title = data['title']
        note.body = data['body']
    else:
        note = NotepadData(
            user_id=current_user.id,
            title= data.get('title', 'To-Do List'),
            body=data['body']
        )
        db.session.add(note)

    db.session.commit()
    return jsonify({'status': 'saved', 'note_id': note.id})

#endregion

#region --- Calendar Routes ---

@app.route('/week-schedule', methods=['GET', 'POST'])
@login_required
def week_schedule():
    add_event_form = AddEventForm()
    dow = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    database_events = db.session.execute(
        select(CalendarEvent)
        .options(selectinload(CalendarEvent.recurring_days))
        .filter(CalendarEvent.user_id == current_user.id)
        .order_by(CalendarEvent.start)
    ).scalars().all()

    edit_event_form = {e.id: EditEventForm(obj=e) for e in database_events}
    events = database_to_calendarview(database_events)
    render_week_schedule(current_user, events)
    image = get_or_create_calendar_image(current_user.id)

    share_calendar_request_form = ShareCalendarRequestForm()
    share_calendar_request_form.image_id.data = image.id

    forms = {
        'add_event_form': add_event_form,
        'edit_event_form': edit_event_form,
        'share_calendar_request_form': share_calendar_request_form,
    }

    if request.method == 'POST':
        if add_event_form.validate_on_submit():
            if (add_event_form.day.data and add_event_form.day_of_week.data) or (not add_event_form.day.data and not add_event_form.day_of_week.data):
                flash("Error selecting days.", 'warning')
                return redirect(url_for('week_schedule'))
            
            start_time = time.fromisoformat(add_event_form.start.data)
            end_time = time.fromisoformat(add_event_form.end.data)

            if add_event_form.day.data:
                conflict = db.session.execute(
                    select(CalendarEvent)
                    .filter(
                        CalendarEvent.user_id == current_user.id,
                        CalendarEvent.day == add_event_form.day.data,
                        CalendarEvent.start < end_time,
                        CalendarEvent.end > start_time
                    )
                ).scalars().first()
            else:
                conflict = db.session.execute(
                    select(CalendarEvent)
                    .join(CalendarEvent.recurring_days)
                    .filter(
                        CalendarEvent.user_id == current_user.id,
                        CalendarEventDay.day_of_week.in_(add_event_form.day_of_week.data),
                        CalendarEvent.start < end_time,
                        CalendarEvent.end > start_time
                    )
                ).scalars().first()

            if conflict:
                flash(f"Conflict with: '{conflict.title}'", 'warning')
                return redirect(url_for('week_schedule'))

            new_event = CalendarEvent(
                user_id=current_user.id,
                title=add_event_form.title.data,
                notes=add_event_form.notes.data,
                day=add_event_form.day.data if add_event_form.day.data else None,
                start=start_time,
                end=end_time,
                color=add_event_form.color.data
            )

            db.session.add(new_event)

            if not add_event_form.day.data and add_event_form.day_of_week.data:
                recurring_days = [
                    CalendarEventDay(day_of_week = day, event = new_event)
                    for day in add_event_form.day_of_week.data
                ]
                db.session.add_all(recurring_days)

            try:
                db.session.commit()
                update_calendar_image(current_user.id)
                flash('Schedule added successfully!', 'success')
            except SQLAlchemyError as e:
                db.session.rollback()
                logging.error(f"Add event to database error: {e}")
                flash('Something went wrong. Please contact support.', 'danger')
                return redirect(url_for('week_schedule'))

            return redirect(url_for('week_schedule'))

    return render_template('week_schedule.html.jinja', **forms, dbe=database_events, dow=dow, image=image.secure_token)

@app.route('/edit-event/<int:event_id>', methods=['POST'])
@login_required
def edit_event(event_id):
    edit_event_form = EditEventForm(request.form)
    if edit_event_form.validate_on_submit():
        event = db.session.get(CalendarEvent, event_id)

        unchanged = (
            edit_event_form.title.data == event.title and
            edit_event_form.notes.data == event.notes and
            edit_event_form.color.data == event.color
        )

        if unchanged:
            flash("No changes detected.", "info")
            return redirect(url_for('week_schedule'))

        if event and event.user_id == current_user.id:
            event.title = edit_event_form.title.data
            event.notes = edit_event_form.notes.data
            event.color = edit_event_form.color.data
            db.session.commit()
            update_calendar_image(current_user.id)
            flash("Update sucessful!", "success")
        else:
            flash("Update unsucessful!", "danger")
    else:
        flash("Form validation failed.", 'warning')
    return redirect(url_for('week_schedule'))

@app.route('/delete-event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = db.session.get(CalendarEvent, event_id)
    if event and event.user_id == current_user.id:
        db.session.delete(event)
        db.session.commit()
        update_calendar_image(current_user.id)
        flash("Event deleted sucessfully!", 'success')
    else:
        flash("Unauthorized", 'danger')
    return redirect(url_for('week_schedule'))

@app.route('/share-calendar-request', methods=['POST'])
@login_required
def share_calendar_request():
    identifier = request.form.get('identifier')
    image_id = request.form.get('image_id')

    user = db.session.execute(
        select(User).filter(
            or_(User.username == identifier, User.email == identifier)
        )
    ).scalar_one_or_none()

    if not user:
        flash("User not found", 'danger')
        return redirect(url_for('week_schedule'))
    
    if user.id == current_user.id:
        flash("You already have access to your own schedule.", 'info')
        return redirect(url_for('week_schedule'))
    
    existing = db.session.execute(
        select(CalendarShare).filter_by(image_id=image_id, viewer_id=user.id)
    ).scalar_one_or_none()

    if existing:
        if existing.status == CalendarShareStatus.PENDING:
            flash("Request previously sent and pending.", 'info')
        elif existing.status == CalendarShareStatus.DECLINED:
            flash("Request previously sent but declined.", 'warning')
        elif existing.status == CalendarShareStatus.ACCEPTED:
            flash("That person already has access.", 'info')
        return redirect(url_for('week_schedule'))
    else:
        share = CalendarShare(image_id=image_id, viewer_id=user.id)
        db.session.add(share)
        db.session.commit()
        flash(f"Share request sent to {identifier}", 'success')
        return redirect(url_for('week_share'))

@app.route('/week-share', methods=['GET', 'POST'])
@login_required
def week_share():

    def get_request_by_status(viewer_id, status):
        return db.session.execute(
            select(CalendarShare)
            .join(CalendarShare.image)
            .filter(CalendarShare.viewer_id == viewer_id)
            .filter(CalendarShare.status == status)
            .order_by(CalendarImage.last_update.desc())
        ).scalars().all()

    accepted_requests = get_request_by_status(current_user.id, CalendarShareStatus.ACCEPTED)
    pending_requests = get_request_by_status(current_user.id, CalendarShareStatus.PENDING)

    sent_requests = db.session.execute(
        select(CalendarShare)
        .join(CalendarImage, CalendarShare.image_id == CalendarImage.id)
        .join(User, CalendarShare.viewer_id == User.id)
        .filter(CalendarImage.owner_id == current_user.id)
        .order_by(CalendarShare.status, User.username)
    ).scalars().all()

    requests = {
        'accepted_requests': accepted_requests,
        'pending_requests': pending_requests,
        'sent_requests': sent_requests,
    }

    share_calendar_response_form = {req.id: ShareCalendarResponseForm(request_id=req.id) for req in pending_requests}

    return render_template('week_share.html.jinja', **requests, share_calendar_response_form=share_calendar_response_form)

@app.route('/share-response/<int:request_id>', methods=['POST'])
@login_required
def share_response(request_id):

    share_calendar_response_form = ShareCalendarResponseForm(request.form)

    if share_calendar_response_form.validate_on_submit():
        share = db.session.get(CalendarShare, request_id)
        if not share or share.viewer_id != current_user.id:
            flash("Unauthorized request.", 'danger')
            return redirect(url_for('week_share'))
        
        if share_calendar_response_form.submit_accept.data:
            share.status = CalendarShareStatus.ACCEPTED
            flash("Calendar share accepted.", 'success')
        elif share_calendar_response_form.submit_decline.data:
            share.status = CalendarShareStatus.DECLINED
            flash("Calendar share declined.", "danger")
        
        db.session.commit()
        return redirect(url_for('week_share'))

@app.route('/delete-calendar-share-request/<int:request_id>', methods=['POST'])
@login_required
def delete_calendar_share_request(request_id):

    share = db.session.execute(
        select(CalendarShare)
        .options(joinedload(CalendarShare.image))
        .where(CalendarShare.id == request_id)
    ).scalar_one_or_none()

    viewer = share.viewer.username

    db.session.delete(share)
    db.session.commit()
    flash(f"Request to share with {viewer} has been removed.", 'success')
    return redirect(url_for('week_share'))

@app.route('/delete-accetped-calendar-share/<int:request_id>', methods=['POST'])
@login_required
def delete_accepted_calendar_share(request_id):

    share = db.session.get(CalendarShare, request_id)

    if not share or share.viewer_id != current_user.id or share.status != CalendarShareStatus.ACCEPTED:
        flash("Unauthorized", 'danger')
        return redirect(url_for('week_share'))
    
    owner_username = share.image.owner.username
    
    db.session.delete(share)
    db.session.commit()
    flash(f"Stopped vieweing {owner_username}'s calendar.", 'info')
    return redirect(url_for('week_share'))

@app.route('/print-calendar/<image>')
@login_required
def print_calendar(image):
    img_source = request.args.get('img_source')
    return render_template('print_calendar.html.jinja', image=image, img_source=img_source)

#endregion

if __name__ == '__main__':
    app.run(debug=True)