from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

login_manager = LoginManager()
mail = Mail()
db = SQLAlchemy(model_class=Base)
csrf = CSRFProtect()
