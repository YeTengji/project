
import secrets
import string
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from flask import current_app
from flask_login import current_user
from flask_mail import Message

from calendar_view.calendar import Calendar
from calendar_view.config import style
from calendar_view.config.style import image_font
from calendar_view.core import data
from calendar_view.core.event import Event, EventStyle, EventStyles

from PIL import ImageFont

from extensions import mail

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
        label = current.strftime("%H:%M")
        choices.append((label,label))
        current += timedelta(minutes=step_minutes)
    if end_field == True:
        choices.append(('23:59', '23:59'))
    return choices

def hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)

def database_to_calendarview(data):
    events = []
    for event in data:
        for recurring_day in event.recurring_days:
            events.append(
                Event(
                    day_of_week=recurring_day.day_of_week,
                    start=event.start.strftime('%H:%M'),
                    end=event.end.strftime('%H:%M'),
                    title=event.title,
                    notes=event.notes,
                    style=EventStyle(
                        event_border=hex_to_rgba(event.color, 240),
                        event_fill=hex_to_rgba(event.color, 192)
                    )
                )
            )
    return events

def image_font(size: int, font_path="static/fonts/LibreBaskerville-Regular.ttf"):
    return ImageFont.truetype(font_path, size)

def render_week_schedule(path, events):
    style.image_bg = (200, 200, 200, 128)
    style.hour_height = 60
    style.title_font = image_font(80)
    style.event_title_font = image_font(32)
    style.day_of_week_font = image_font(32)

    config = data.CalendarConfig(
        lang='en',
        title=f"{current_user.first_name}'s Schedule",
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