from datetime import datetime, timezone
from typing import List
from werkzeug.security import check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(256),nullable=False)
    creation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    update_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    theme = relationship('UserTheme', back_populates='user', cascade='all, delete-orphan', uselist=False)
    reset_codes = relationship('ResetCode', back_populates='user', cascade='all, delete-orphan')
    previous_passwords: Mapped[List['PreviousPassword']] = relationship(back_populates='user', cascade='all, delete-orphan')

    def has_used_password(self, raw_password: str, limit: int = 5) -> bool:
        recent = sorted(self.previous_passwords, key=lambda p: p.change_date, reverse=True)[:limit]
        return any(check_password_hash(p.previous_password, raw_password) for p in recent)

    def __repr__(self):
        return f'<User {self.username}>'
    
class UserTheme(db.Model):
    __tablename__ = 'user_theme'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, unique=True)
    theme: Mapped[str] = mapped_column(String(8), nullable=False, default='dark')
    user = relationship('User', back_populates='theme')

class ResetCode(db.Model):
    __tablename__ = 'reset_codes'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    requested: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expiration: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(default=False)
    user: Mapped['User'] = relationship(back_populates='reset_codes')

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expiration

class PreviousPassword(db.Model):
    __tablename__ = 'previous_passwords'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    previous_password: Mapped[str] = mapped_column(String(256),nullable=False)
    change_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user: Mapped['User'] = relationship(back_populates='previous_passwords')



