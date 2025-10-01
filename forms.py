from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, ValidationError
from flask_login import current_user
from sqlalchemy import func, select
from models import db, User

class LoginForm(FlaskForm):
    form_type = HiddenField('Form Type', default='login')
    identifier = StringField('Username or Email', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Log In')

class SignUpForm(FlaskForm):
    form_type = HiddenField('Form Type', default='signup')
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=64)])
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=32),
        Regexp(r'^[A-Za-z][A-Za-z0-9]*$', message="Username must be alphanumeric, start with a letter, and have no spaces.")
        ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters."),
        Regexp(r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]).+$',
            message="Password must include a capital letter, a number, and a special character.")
        ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
        ])
    theme = HiddenField('Theme', default='dark')
    submit = SubmitField('Sign Up')

    def validate_username(self, field):
        stmt = select(User).where(func.lower(User.username) == field.data.lower())
        user = db.session.execute(stmt).scalar_one_or_none()
        if user:
            raise ValidationError("Invalid username.")

class UserProfileForm(FlaskForm):
    form_type = HiddenField('Form Type', default='user-profile')
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=64)])
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=32),
        Regexp(r'^[A-Za-z][A-Za-z0-9]*$', message="Username must be alphanumeric, start with a letter, and have no spaces.")
        ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

    def validate_username(self, field):
        stmt = select(User).where(func.lower(User.username) == field.data.lower())
        user = db.session.execute(stmt).scalar_one_or_none()
        if user and user.id != current_user.id:
            raise ValidationError("Please create a diffrenent username.")
        
class ForgotPasswordForm(FlaskForm):
    form_type = HiddenField('Form Type', default='forgot-password')
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Code')

class VerifyPasswordResetCodeForm(FlaskForm):
    form_type = HiddenField('Form Type', default='verify-password-reset-code')
    code = StringField('Reset Code', validators=[
        DataRequired(),
        Length(min=6, max=6, message="Code must be 6 characters."),
        Regexp(r'^[A-Z0-9]{6}$', message="Invalid code.")
        ])
    submit = SubmitField('Verify Code')

class ResetPasswordForm(FlaskForm):
    form_type = HiddenField('Form Type', default='reset-password')
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters."),
        Regexp(r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]).+$',
            message="Password must include a capital letter, a number, and a special character.")
        ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
        ])
    submit = SubmitField('Reset Password')

class ChangePasswordForm(ResetPasswordForm):
    form_type = HiddenField('Form Type', default='change-password')
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')