import secrets
import string

# --- Generate Six Character Code ---
def generate_secure_code(length=6):
    chars = string.ascii_uppercase + string.digits

    return ''.join(secrets.choice(chars) for _ in range(length))

