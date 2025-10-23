import enum

from datetime import date, datetime, time, timezone
from typing import List
from werkzeug.security import check_password_hash
from flask_login import UserMixin
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from extensions import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(256),nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    time_zone: Mapped[str] = mapped_column(String(64), nullable=False)
    creation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    update_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    theme = relationship('UserTheme', back_populates='user', cascade='all, delete-orphan', uselist=False)
    reset_codes = relationship('ResetCode', back_populates='user', cascade='all, delete-orphan')
    previous_passwords: Mapped[List['PreviousPassword']] = relationship(back_populates='user', cascade='all, delete-orphan')
    calendar_events = relationship('CalendarEvent', back_populates='user', cascade='all, delete-orphan')

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
    previous_password: Mapped[str] = mapped_column(String(256), nullable=False)
    change_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user: Mapped['User'] = relationship(back_populates='previous_passwords')

class CalendarEvent(db.Model):
    __tablename__ = 'calendar_events'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    title: Mapped[str] = mapped_column(String(24), nullable=False)
    notes: Mapped[str] = mapped_column(String(64), nullable=True)
    start: Mapped[time] = mapped_column(Time(), nullable=False)
    end: Mapped[time] = mapped_column(Time(), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    day: Mapped[date] = mapped_column(Date(), nullable=True)

    user = relationship('User', back_populates='calendar_events')
    recurring_days = relationship('CalendarEventDay', back_populates='event', cascade='all, delete-orphan')

class CalendarEventDay(db.Model):
    __tablename__ = 'calendar_event_days'
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="valid_day_of_week"),
        UniqueConstraint("event_id", "day_of_week", name="unique_event_day")
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey('calendar_events.id'), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    event = relationship('CalendarEvent', back_populates='recurring_days')

class CalendarImage(db.Model):
    __tablename__ = 'calendar_images'

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    secure_token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    last_update: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    owner = relationship('User', backref='calendar_images')
    viewers = relationship('CalendarShare', back_populates='image')

class CalendarShareStatus(enum.IntEnum):
    DECLINED = 0
    PENDING = 1
    ACCEPTED = 2

    def label(self):
        return {
            self.DECLINED: 'Declined',
            self.PENDING: 'Waiting',
            self.ACCEPTED: 'Accepted'
        }[self]

class CalendarShare(db.Model):
    __tablename__ = 'calendar_shares'

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(ForeignKey('calendar_images.id'), nullable=False)
    viewer_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    status: Mapped[CalendarShareStatus] = mapped_column(Integer, default=CalendarShareStatus.PENDING)

    image = relationship('CalendarImage', back_populates='viewers')
    viewer = relationship('User', backref='received_calendar_images')

