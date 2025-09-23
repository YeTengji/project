from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

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
    ### consider Regexp for alphabetic validation
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
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    theme = HiddenField('Theme', default='dark')
    submit = SubmitField('Sign Up')