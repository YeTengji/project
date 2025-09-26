from flask_login import current_user

from models import db, User
from forms import UserProfileForm

def inject_user_profile_form():
    if current_user.is_authenticated:
        user = db.session.get(User, current_user.id)
        return dict(user_profile_form=UserProfileForm(obj=user))
    return dict(user_profile_form=None)