import os
from datetime import timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_wtf import CSRFProtect
from sqlalchemy import select, or_, func
from sqlalchemy.exc import SQLAlchemyError

from forms import LoginForm, SignUpForm
from models import db, User, UserTheme

load_dotenv()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)

    login_manager.init_app(app)
    login_manager.login_view = 'login'
    db.init_app(app)
    csrf.init_app(app)
    with app.app_context():
        db.create_all()

    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def root():
    return redirect(url_for('login'))

# -------- Authentication and Registration Routes --------
## --- Login with SignUp Modal
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    login_form = LoginForm()
    signup_form = SignUpForm()

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'login' and login_form.validate_on_submit():
            identifier = login_form.identifier.data.strip()

            stmt = select(User).where(or_(User.username == identifier, func.lower(User.email) == identifier.lower()))
            user = db.session.execute(stmt).scalar_one_or_none()
            if user and check_password_hash(user.password, login_form.password.data):
                login_user(user, remember=login_form.remember.data)
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials.', 'danger')
                return redirect(url_for('login'))
        
        elif form_type =='signup' and signup_form.validate_on_submit():
            existing_user = db.session.execute(select(User).where(func.lower(User.username) == signup_form.username.data.lower())).scalar_one_or_none()
            if existing_user:
                flash('Username already taken.', 'danger')
                return render_template('login.html', login_form=login_form, signup_form=signup_form)
            
            existing_email = db.session.execute(select(User).where(func.lower(User.email) == signup_form.email.data.lower())).scalar_one_or_none()
            if existing_email:
                flash('Email already registered. Please log in.', 'danger')
                return redirect(url_for('login'))
            
            new_user = User(
                first_name=signup_form.first_name.data.strip(),
                last_name=signup_form.last_name.data.strip(),
                username=signup_form.username.data,
                email=signup_form.email.data.strip().lower(),
                password=generate_password_hash(signup_form.password.data)
            )

            user_theme = UserTheme(theme=signup_form.theme.data)
            new_user.theme = user_theme

            try:
                db.session.add(new_user)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                print(f"Database error: {e}")
                flash('Something went wrong. Please try again.', 'danger')
                return redirect(url_for('login'))
            
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
        
    return render_template('login.html', login_form=login_form, signup_form=signup_form)

# -------- User Routes --------
## --- Logout ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout Successful.', 'info')

    return redirect(url_for('login'))

## --- Theme Update ---
@app.route('/update-theme', methods=['POST'])
@login_required
def update_theme():
    data = request.get_json()
    new_theme = data.get('theme')

    if new_theme not in ['light', 'dark']:
        return jsonify({'error': 'Invalid theme'}), 400
    
    user_theme = UserTheme.query.filter_by(user_id=current_user.id).first()
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

## --- Dashboard Route ---
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)