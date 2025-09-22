import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_wtf import CSRFProtect
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
## --- Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    login_form = LoginForm()
    signup_form = SignUpForm()

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'login' and login_form.validate_on_submit():
            user = User.query.filter_by(username=login_form.username.data).first()
            if user and check_password_hash(user.password, login_form.password.data):
                login_user(user)
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials.', 'danger')
                return redirect(url_for('login'))
        
        elif form_type =='signup' and signup_form.validate_on_submit():
            existing_user = User.query.filter_by(username=signup_form.username.data).first()
            if existing_user:
                flash('Username already taken.', 'danger')
                return render_template('login.html', login_form=login_form, signup_form=signup_form)
            
            existing_email = User.query.filter_by(email=signup_form.email.data.lower()).first()
            if existing_email:
                flash('Email already registered. Please log in.', 'danger')
                return redirect(url_for('login'))
            
            new_user = User(
                first_name=signup_form.first_name.data.strip(),
                last_name=signup_form.last_name.data.strip(),
                username=signup_form.username.data,
                email=signup_form.email.data.lower(),
                password=generate_password_hash(signup_form.password.data)
            )

            try:
                db.session.add(new_user)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                print(f"Database error: {e}")
                flash('Something went wrong. Please try again.', 'danger')
                return redirect(url_for('signup'))
            
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
        
    return render_template('login.html', login_form=login_form, signup_form=signup_form)

## --- Logout ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout Successful.', 'info')

    return redirect(url_for('login'))

# -------- User Routes --------
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