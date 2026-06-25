"""
games.py — Game CRUD operations for Game Event Desktop App.
"""

import os
from backend.database import get_connection

# Path to game logos folder
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGOS_DIR = os.path.join(APP_DIR, "game_logos")


def get_all_games():
    """Fetch all games from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM games ORDER BY game_name ASC")
    games = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return games


def get_game_by_id(game_id):
    """Fetch a single game by its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM games WHERE game_id = ?", (game_id,))
    game = cursor.fetchone()
    conn.close()
    return dict(game) if game else None


def add_game(game_name):
    """
    Add a new game to the database.
    Returns (success: bool, message: str)
    """
    if not game_name or not game_name.strip():
        return False, "Game name cannot be empty."

    game_name = game_name.strip()

    conn = get_connection()
    cursor = conn.cursor()

    # Check for duplicate
    cursor.execute("SELECT game_id FROM games WHERE game_name = ?", (game_name,))
    if cursor.fetchone():
        conn.close()
        return False, f"Game '{game_name}' already exists."

    cursor.execute("INSERT INTO games (game_name) VALUES (?)", (game_name,))
    conn.commit()
    conn.close()

    return True, f"Game '{game_name}' added successfully!"


def delete_game(game_id):
    """Delete a game from the database."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if any events reference this game
    cursor.execute("SELECT COUNT(*) as cnt FROM events WHERE game_id = ?", (game_id,))
    count = cursor.fetchone()['cnt']
    if count > 0:
        conn.close()
        return False, "Cannot delete game: it has associated events."

    cursor.execute("DELETE FROM games WHERE game_id = ?", (game_id,))
    conn.commit()
    conn.close()
    return True, "Game deleted."


def get_game_logo_path(game_name):
    """
    Get the file path to a game's logo image.
    Returns the path if found, None otherwise.
    Checks for .png first, then .jpg, then .jpeg.
    """
    if not game_name:
        return None

    # Ensure logos directory exists
    os.makedirs(LOGOS_DIR, exist_ok=True)

    for ext in ['.png', '.jpg', '.jpeg']:
        path = os.path.join(LOGOS_DIR, f"{game_name}{ext}")
        if os.path.isfile(path):
            return path

    return None
