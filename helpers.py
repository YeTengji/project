import requests
import secrets
import string
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from flask import current_app
from flask_login import current_user
from flask_mail import Message

from sqlalchemy import select

from calendar_view.calendar import Calendar
from calendar_view.config import style
from calendar_view.config.style import image_font
from calendar_view.core import data
from calendar_view.core.event import Event, EventStyle

from PIL import ImageFont

from extensions import db, mail
from models import CalendarImage

#region --- Functions ---
# --- Generate Six Character Code ---
def generate_secure_code(length=6):
    chars = string.ascii_uppercase + string.digits

    return ''.join(secrets.choice(chars) for _ in range(length))

# --- Send Reset Code Via Email ---
def send_reset_code_email(recipient_email, code):
    msg = Message(
        subject="Your Password Reset Code",
        recipients=[recipient_email],
        body=f"""Hi,

Here is your password reset code:

🔐 {code}

This code will expire in 15 minutes.

— {current_app.config.get('APP_NAME', 'I.G.K.H.')} Team
"""
    )
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Email send failed: {e}")

#endregion

#region --- Calendar Functions ---
def get_user_week_range(user):
    today = datetime.now(ZoneInfo(user.time_zone))
    start = today - timedelta(days=today.weekday() + 1 if today.weekday != 6 else 0)
    end = start + timedelta(days=6)
    return f"{start.strftime('%Y-%m-%d')} - {end.strftime('%Y-%m-%d')}"

def generate_time_choices(start_hour=0, end_hour=23, step_minutes=30, end_field=False):
    choices = []
    current = datetime.strptime(f"{start_hour:02}:00", "%H:%M")
    end = datetime.strptime(f"{end_hour:02}:30", "%H:%M")

    while current <= end:
        label = current.strftime("%I:%M %p")
        value = current.strftime("%H:%M")
        choices.append((value,label))
        current += timedelta(minutes=step_minutes)
    if end_field == True:
        choices.append(('23:59', '11:59 PM'))
    return choices

def hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)

def database_to_calendarview(data):
    events = []
    today = datetime.now().date()
    start = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
    end = start + timedelta(days=6)

    one_time_events_by_weekday = {}
    for event in data:
        if event.day:

            if not (start <= event.day <= end):
                continue

            weekday = event.day.weekday()
            one_time_events_by_weekday.setdefault(weekday, []).append(event)

            start_str = event.start.strftime('%I:%M %p')
            end_str = event.end.strftime('%I:%M %p')
            title_with_time = f"{event.title}\n{start_str} - {end_str}"

            events.append(
                Event(
                    day=event.day.strftime('%Y-%m-%d'),
                    start=event.start.strftime('%H:%M'),
                    end=event.end.strftime('%H:%M'),
                    title=title_with_time,
                    notes=event.notes,
                    style=EventStyle(
                        event_border=hex_to_rgba(event.color, 240),
                        event_fill=hex_to_rgba(event.color, 192)
                    )
                )
            )

    for event in data:
        for recurring_day in event.recurring_days:
            weekday = recurring_day.day_of_week

            overlaps = False
            for one_time_event in one_time_events_by_weekday.get(weekday, []):
                if event.start < one_time_event.end and event.end > one_time_event.start:
                    overlaps = True
                    break
                
            if overlaps:
                continue

            start_str = event.start.strftime('%I:%M %p')
            end_str = event.end.strftime('%I:%M %p')
            title_with_time = f"{event.title}\n{start_str} - {end_str}"

            events.append(
                Event(
                    day_of_week=weekday,
                    start=event.start.strftime('%H:%M'),
                    end=event.end.strftime('%H:%M'),
                    title=title_with_time,
                    notes=event.notes,
                    style=EventStyle(
                        event_border=hex_to_rgba(event.color, 240),
                        event_fill=hex_to_rgba(event.color, 192)
                    )
                )
            )
    return events

def generate_unique_token():
    while True:
        token = secrets.token_urlsafe(48)[:64]
        exists = db.session.execute(
            select(CalendarImage)
            .filter_by(secure_token=token)
        ).scalar_one_or_none()
        if not exists:
            return token

def get_or_create_calendar_image(user_id):
    image = db.session.execute(
        select(CalendarImage)
        .filter(CalendarImage.owner_id == user_id)
    ).scalar_one_or_none()
    if image:
        return image
    token = generate_unique_token()
    image = CalendarImage(owner_id=user_id, secure_token=token, last_update=date.today())
    db.session.add(image)
    db.session.commit()
    return image

def update_calendar_image(user_id):
    image = db.session.execute(
        select(CalendarImage)
        .filter(CalendarImage.owner_id == user_id)
    ).scalar_one_or_none()
    if image:
        image.last_update = date.today()
        db.session.commit()

def image_font(size: int, font_path="static/fonts/LibreBaskerville-Regular.ttf"):
    return ImageFont.truetype(font_path, size)

def render_week_schedule(user, events):
    image = get_or_create_calendar_image(user.id)
    path = f"static/images/calendar/{image.secure_token}.png"
    style.image_bg = (200, 200, 200, 128)
    style.hour_height = 60
    style.title_font = image_font(80)
    style.event_title_font = image_font(25)
    style.day_of_week_font = image_font(32)

    config = data.CalendarConfig(
        lang='en',
        title=f"{current_user.username}'s Schedule",
        dates=get_user_week_range(current_user),
        hours='0 - 24',
        show_date=True,
        show_year = True,
        legend=False,
        title_vertical_align='center'
    )
    ''' events = [
        Event(day_of_week=0, start='08:00', end='12:30', title='First half', notes='work x 3', style=EventStyles.BLUE),
        Event(day_of_week=3, start='13:00', end='16:30', title='Another Year', notes='HBD', style=EventStyles.RED),
        Event(day='2025-10-08', start='22:00', end='23:00', title='Close to Midnight', notes='Nothing Else Matters So Close', style=EventStyle(event_border=(250, 250, 250, 240),event_fill=(200, 200, 100, 190))),
    ] '''

    calendar = Calendar.build(config)
    calendar.add_events(events)
    calendar.save(path)

#endregion ---

#region --- APIs ---

def inspire():
    url = "https://zenquotes.io/api/today"
    print("Quote retrieval successful.")
    try:
        response = requests.get(url)
        response.raise_for_status()
        inspiration = response.json()
        return inspiration
    except requests.RequestException as e:
        print(f"Request error: {e}")
    except (KeyError, ValueError) as e:
        print(f"Data parsing error: {e}")
    return None