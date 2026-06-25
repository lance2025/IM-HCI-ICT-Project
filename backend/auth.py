"""
auth.py — Login, signup, and role logic for Game Event Desktop App.
"""

from backend.database import get_connection, hash_password


class Session:
    """Stores current user session information."""
    _instance = None

    def __init__(self):
        self.user_id = None
        self.username = None
        self.role = None
        self.user_timezone = None
        self.is_logged_in = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def login(self, user_id, username, role, user_timezone):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.user_timezone = user_timezone
        self.is_logged_in = True

    def logout(self):
        self.user_id = None
        self.username = None
        self.role = None
        self.user_timezone = None
        self.is_logged_in = False

    @property
    def is_admin(self):
        return self.role == 'admin'


def authenticate(username, pw):
    """
    Authenticate a user with username and password.
    Returns (success: bool, message: str, user_data: dict or None)
    """
    if not username or not pw:
        return False, "Username and password are required.", None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user is None:
        return False, "User not found. Check your username.", None

    if user['password_hash'] != hash_password(pw):
        return False, "Incorrect password.", None

    user_data = {
        'user_id': user['user_id'],
        'username': user['username'],
        'role': user['role'],
        'user_timezone': user['user_timezone']
    }

    return True, "Login successful!", user_data


def signup(username, pw, timezone='UTC'):
    """
    Register a new user account.
    Returns (success: bool, message: str)
    """
    if not username or not pw:
        return False, "Username and password are required."

    if len(username) < 3:
        return False, "Username must be at least 3 characters."

    if len(pw) < 4:
        return False, "Password must be at least 4 characters."

    if username.lower() == 'admin':
        return False, "Cannot register with username 'admin'."

    conn = get_connection()
    cursor = conn.cursor()

    # Check if username exists
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username already taken. Choose another."

    # Create user
    pw_hashed = hash_password(pw)
    cursor.execute("""
        INSERT INTO users (username, password_hash, role, user_timezone)
        VALUES (?, ?, 'user', ?)
    """, (username, pw_hashed, timezone))

    conn.commit()
    conn.close()

    return True, "Account created successfully! You can now log in."


def get_all_timezones():
    """Return a list of common timezone strings."""
    return [
        "UTC",
        "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
        "Europe/London", "Europe/Paris", "Europe/Berlin",
        "Asia/Tokyo", "Asia/Shanghai", "Asia/Singapore", "Asia/Manila",
        "Asia/Kolkata", "Asia/Dubai",
        "Australia/Sydney", "Australia/Melbourne",
        "Pacific/Auckland",
        "America/Sao_Paulo", "America/Toronto", "America/Chicago",
        "Africa/Cairo", "Africa/Lagos"
    ]
