"""
events.py — Event CRUD operations for Game Event Desktop App.
"""

from backend.database import get_connection


def create_event(event_data):
    """
    Create a new event.
    event_data: dict with all event fields.
    Returns (success: bool, message: str)
    """
    required = ['event_name', 'game_id', 'event_date']
    for field in required:
        if not event_data.get(field):
            return False, f"Field '{field}' is required."

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO events (
                created_by, game_id, event_name, event_theme, description,
                event_date, end_date, start_time, end_time, source_timezone,
                location_type, venue, online_platform, online_link,
                region, status, is_archived, recurring,
                max_participants, registration_link, availability,
                prize_pool, entry_fee_type, entry_fee_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_data.get('created_by'),
            event_data.get('game_id'),
            event_data.get('event_name', ''),
            event_data.get('event_theme', ''),
            event_data.get('description', ''),
            event_data.get('event_date', ''),
            event_data.get('end_date', ''),
            event_data.get('start_time', ''),
            event_data.get('end_time', ''),
            event_data.get('source_timezone', 'UTC'),
            event_data.get('location_type', 'online'),
            event_data.get('venue', ''),
            event_data.get('online_platform', ''),
            event_data.get('online_link', ''),
            event_data.get('region', ''),
            event_data.get('status', 'Upcoming'),
            0,  # is_archived
            event_data.get('recurring', 'none'),
            event_data.get('max_participants', 0),
            event_data.get('registration_link', ''),
            event_data.get('availability', 'open'),
            event_data.get('prize_pool', ''),
            event_data.get('entry_fee_type', 'free'),
            event_data.get('entry_fee_amount', '')
        ))

        conn.commit()
        conn.close()
        return True, "Event created successfully!"
    except Exception as e:
        return False, f"Database error: {type(e).__name__}: {e}"


def get_active_events(search_query=None, date_filter=None):
    """Fetch all non-archived events (ongoing/upcoming)."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT e.*, g.game_name
        FROM events e
        LEFT JOIN games g ON e.game_id = g.game_id
        WHERE e.is_archived = 0
    """
    params = []

    if search_query:
        query += " AND (e.event_name LIKE ? OR g.game_name LIKE ? OR e.event_theme LIKE ?)"
        like = f"%{search_query}%"
        params.extend([like, like, like])

    if date_filter:
        # Show events where the selected date falls within their start→end range
        query += """ AND (
            e.event_date <= ? AND (e.end_date >= ? OR e.end_date = '' OR e.end_date IS NULL)
        )"""
        params.extend([date_filter, date_filter])

    query += " ORDER BY e.event_date ASC, e.start_time ASC"

    cursor.execute(query, params)
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return events


def get_archived_events(search_query=None, date_filter=None):
    """Fetch all archived events."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT e.*, g.game_name
        FROM events e
        LEFT JOIN games g ON e.game_id = g.game_id
        WHERE e.is_archived = 1
    """
    params = []

    if search_query:
        query += " AND (e.event_name LIKE ? OR g.game_name LIKE ? OR e.event_theme LIKE ?)"
        like = f"%{search_query}%"
        params.extend([like, like, like])

    if date_filter:
        # Show events where the selected date falls within their start→end range
        query += """ AND (
            e.event_date <= ? AND (e.end_date >= ? OR e.end_date = '' OR e.end_date IS NULL)
        )"""
        params.extend([date_filter, date_filter])

    query += " ORDER BY e.event_date DESC"

    cursor.execute(query, params)
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return events


def get_event_by_id(event_id):
    """Fetch a single event by its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, g.game_name
        FROM events e
        LEFT JOIN games g ON e.game_id = g.game_id
        WHERE e.event_id = ?
    """, (event_id,))
    event = cursor.fetchone()
    conn.close()
    return dict(event) if event else None


def update_event(event_id, event_data):
    """Update an existing event."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE events SET
                game_id = ?, event_name = ?, event_theme = ?, description = ?,
                event_date = ?, end_date = ?, start_time = ?, end_time = ?, source_timezone = ?,
                location_type = ?, venue = ?, online_platform = ?, online_link = ?,
                region = ?, status = ?, recurring = ?,
                max_participants = ?, registration_link = ?, availability = ?,
                prize_pool = ?, entry_fee_type = ?, entry_fee_amount = ?
            WHERE event_id = ?
        """, (
            event_data.get('game_id'),
            event_data.get('event_name', ''),
            event_data.get('event_theme', ''),
            event_data.get('description', ''),
            event_data.get('event_date', ''),
            event_data.get('end_date', ''),
            event_data.get('start_time', ''),
            event_data.get('end_time', ''),
            event_data.get('source_timezone', 'UTC'),
            event_data.get('location_type', 'online'),
            event_data.get('venue', ''),
            event_data.get('online_platform', ''),
            event_data.get('online_link', ''),
            event_data.get('region', ''),
            event_data.get('status', 'Upcoming'),
            event_data.get('recurring', 'none'),
            event_data.get('max_participants', 0),
            event_data.get('registration_link', ''),
            event_data.get('availability', 'open'),
            event_data.get('prize_pool', ''),
            event_data.get('entry_fee_type', 'free'),
            event_data.get('entry_fee_amount', ''),
            event_id
        ))

        conn.commit()
        conn.close()
        return True, "Event updated successfully!"
    except Exception as e:
        return False, f"Database error: {type(e).__name__}: {e}"


def delete_event(event_id):
    """Delete an event."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
    conn.commit()
    conn.close()
    return True, "Event deleted."


def get_events_for_month(year, month):
    """Get all days in a given month that have events (including multi-day spans)."""
    from datetime import date, timedelta

    conn = get_connection()
    cursor = conn.cursor()

    month_str = f"{year:04d}-{month:02d}"

    # Get events that overlap with this month:
    # - event_date is in this month, OR
    # - end_date is in this month, OR
    # - event spans across this month (starts before, ends after)
    cursor.execute("""
        SELECT event_date, end_date FROM events
        WHERE is_archived = 0
          AND (event_date LIKE ? OR end_date LIKE ?
               OR (event_date < ? AND (end_date >= ? OR end_date = '')))
    """, (f"{month_str}%", f"{month_str}%",
          f"{month_str}-32", f"{month_str}-01"))

    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    dates = set()
    for row in cursor.fetchall():
        try:
            start = date.fromisoformat(row['event_date'])
            end = date.fromisoformat(row['end_date']) if row['end_date'] else start
            # Clamp to this month
            day = max(start, month_start)
            end_clamped = min(end, month_end)
            while day <= end_clamped:
                dates.add(day.isoformat())
                day += timedelta(days=1)
        except (ValueError, TypeError):
            continue

    conn.close()
    return list(dates)
