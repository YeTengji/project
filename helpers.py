import secrets
import string

from flask import current_app
from flask_mail import Mail, Message

mail = Mail()

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
