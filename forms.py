import pytz
import pycountry

from datetime import date

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DateTimeField, HiddenField, PasswordField, SelectField, SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp, ValidationError
from wtforms.widgets import CheckboxInput, ListWidget
from flask_login import current_user
from sqlalchemy import func, select

from helpers import generate_time_choices
from models import db, User

country_choices = sorted([(c.alpha_2, c.name) for c in pycountry.countries], key=lambda x: x[1])
timezone_choices = sorted([(tz, tz) for tz in pytz.common_timezones])
start_time_choices = generate_time_choices()
end_time_choices = generate_time_choices(end_field=True)

class LoginForm(FlaskForm):
    form_type = HiddenField('Form Type', default='login')
    identifier = StringField('Username or Email', validators=[DataRequired(), Length(min=3, max=64)], render_kw={"placeholder": "Username or Email"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Password"})
    remember = BooleanField('Remember me')
    theme = HiddenField('Theme')
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
    country = SelectField('Country', choices=country_choices, validators=[DataRequired()])
    time_zone = SelectField('Time Zone', choices=timezone_choices, validators=[DataRequired()])
    theme = HiddenField('Theme', default='dark')
    submit = SubmitField('Sign Up')

    def validate_username(self, field):
        stmt = select(User).where(func.lower(User.username) == field.data.lower())
        user = db.session.execute(stmt).scalar_one_or_none()
        if user:
            raise ValidationError("Invalid username.")
        
    def validate_country(self, field):
        if not pycountry.countries.get(alpha_2=field.data):
            raise ValidationError("Invalid country code.")

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
    country = SelectField('Country', choices=country_choices, validators=[DataRequired()])
    time_zone = SelectField('Time Zone', choices=timezone_choices, validators=[DataRequired()])
    submit = SubmitField('Update')

    def validate_username(self, field):
        stmt = select(User).where(func.lower(User.username) == field.data.lower())
        user = db.session.execute(stmt).scalar_one_or_none()
        if user and user.id != current_user.id:
            raise ValidationError("Please create a diffrenent username.")

    def validate_country(self, field):
        if not pycountry.countries.get(alpha_2=field.data):
            raise ValidationError("Invalid country code.")
        
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

class AddEventForm(FlaskForm):
    form_type = HiddenField('Form Type', default='add-event')
    title = StringField('Title', validators=[DataRequired(), Length (min=1, max=24)])
    notes = StringField('Notes', validators=[DataRequired(), Length(min=1, max=64)])
    day_of_week = SelectMultipleField(
        'Day(s) of the Week',
        choices=[
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday'),
        ],
        coerce=int,
        validators=[Optional()],
        option_widget=CheckboxInput(),
        widget=ListWidget(prefix_label=False)
    )
    start = SelectField('Start Time', choices=start_time_choices, validators=[DataRequired()])
    end = SelectField('End Time', choices=end_time_choices, validators=[DataRequired()])
    color = StringField('Color', default='#0F52BA', render_kw={'type': 'color'}, validators=[DataRequired(), Length(max=7)])
    submit = SubmitField('Add Event')

    def validate(self, extra_validators=None):
        is_valid = super().validate(extra_validators)
        return is_valid

class EditEventForm(FlaskForm):
    form_type = HiddenField('Form Type', default='edit-event')
    title = StringField('Title', validators=[DataRequired(), Length (min=1, max=24)])
    notes = StringField('Notes', validators=[DataRequired(), Length(min=1, max=64)])
    color = StringField('Color', default='#0F52BA', render_kw={'type': 'color'}, validators=[DataRequired(), Length(max=7)])
    submit = SubmitField("Update")