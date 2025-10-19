from flask import request
from flask_login import current_user

from models import db, CalendarShareStatus, User
from forms import UserProfileForm

def inject_theme_from_cookie():
    theme = request.cookies.get('theme', 'dark')
    return {'cookie_theme': theme}

def inject_user_profile_form():
    if current_user.is_authenticated:
        user = db.session.get(User, current_user.id)
        return dict(user_profile_form=UserProfileForm(obj=user))
    return dict(user_profile_form=None)

def inject_calendar_share_status_enums():
    return dict(CalendarShareStatus=CalendarShareStatus)

