"""
database.py — SQLite connection, table creation, and seeding for Game Event Desktop App.
"""

import sqlite3
import os
import hashlib
from datetime import datetime

# Database path relative to the app's root directory
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(APP_DIR, "gameevents_desktop.db")


def get_connection():
    """Get a new SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(pw):
    """Hash a password using SHA-256."""
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()


def init_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('admin', 'user')),
            user_timezone TEXT DEFAULT 'UTC',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Games table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_by INTEGER,
            game_id INTEGER,
            event_name TEXT NOT NULL,
            event_theme TEXT DEFAULT '',
            description TEXT DEFAULT '',
            event_date TEXT NOT NULL,
            end_date TEXT DEFAULT '',
            start_time TEXT DEFAULT '',
            end_time TEXT DEFAULT '',
            source_timezone TEXT DEFAULT 'UTC',
            location_type TEXT DEFAULT 'online' CHECK(location_type IN ('physical', 'online')),
            venue TEXT DEFAULT '',
            online_platform TEXT DEFAULT '',
            online_link TEXT DEFAULT '',
            region TEXT DEFAULT '',
            status TEXT DEFAULT 'Upcoming' CHECK(status IN ('Upcoming', 'Ongoing', 'Finished', 'Cancelled')),
            is_archived INTEGER DEFAULT 0,
            recurring TEXT DEFAULT 'none' CHECK(recurring IN ('none', 'weekly', 'monthly', 'yearly')),
            max_participants INTEGER DEFAULT 0,
            registration_link TEXT DEFAULT '',
            availability TEXT DEFAULT 'open' CHECK(availability IN ('open', 'invite_only', 'members_only')),
            prize_pool TEXT DEFAULT '',
            entry_fee_type TEXT DEFAULT 'free' CHECK(entry_fee_type IN ('free', 'paid')),
            entry_fee_amount TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (created_by) REFERENCES users(user_id),
            FOREIGN KEY (game_id) REFERENCES games(game_id)
        )
    """)

    conn.commit()
    conn.close()


def seed_database():
    """Seed the database with default admin and pre-defined games."""
    conn = get_connection()
    cursor = conn.cursor()

    # Seed admin user (only if not exists)
    admin_hash = hash_password("admin123")
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password_hash, role, user_timezone)
        VALUES (?, ?, 'admin', 'UTC')
    """, ("admin", admin_hash))

    # Pre-seeded games
    games = [
        "Minecraft", "Valorant", "League of Legends", "Genshin Impact",
        "Roblox", "Tekken", "Counter-Strike 2", "Dota 2", "Fortnite",
        "Apex Legends", "PUBG", "Overwatch 2", "Rocket League", "Street Fighter 6"
    ]

    for game in games:
        cursor.execute("INSERT OR IGNORE INTO games (game_name) VALUES (?)", (game,))

    conn.commit()
    conn.close()


def initialize():
    """Full initialization: create tables + seed data."""
    init_database()
    seed_database()


if __name__ == "__main__":
    initialize()
    print(f"Database initialized at: {DB_PATH}")
