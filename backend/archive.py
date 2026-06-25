"""
archive.py — Auto-archiving logic for Game Event Desktop App.
Uses end_date (if set) to determine when an event actually ends.
- Events whose end_date/event_date is >7 days past: move to archived.
- Events whose end_date/event_date is past but within 7 days: mark as "Finished".
- Events happening today (between start and end date): mark as "Ongoing".
"""

from datetime import datetime, timedelta
from backend.database import get_connection


def run_auto_archive():
    """
    Check all non-archived events and apply archiving rules.
    Uses end_date if available, otherwise falls back to event_date.
    """
    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=7)

    # Get all non-archived events
    cursor.execute("""
        SELECT event_id, event_date, end_date, status FROM events
        WHERE is_archived = 0 AND status != 'Cancelled'
    """)

    events = cursor.fetchall()

    for event in events:
        try:
            start_date = datetime.strptime(event['event_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            continue

        # Use end_date if it exists and is valid, otherwise use event_date
        end_date = start_date
        if event['end_date']:
            try:
                end_date = datetime.strptime(event['end_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if end_date < seven_days_ago:
            # More than 7 days past end → archive it
            cursor.execute("""
                UPDATE events SET is_archived = 1, status = 'Finished'
                WHERE event_id = ?
            """, (event['event_id'],))
        elif end_date < today:
            # Past end but within 7 days → mark as Finished, keep visible
            if event['status'] not in ('Finished', 'Cancelled'):
                cursor.execute("""
                    UPDATE events SET status = 'Finished'
                    WHERE event_id = ?
                """, (event['event_id'],))
        elif start_date <= today <= end_date:
            # Currently happening (between start and end) → mark as Ongoing
            if event['status'] not in ('Ongoing', 'Cancelled'):
                cursor.execute("""
                    UPDATE events SET status = 'Ongoing'
                    WHERE event_id = ?
                """, (event['event_id'],))
        elif start_date > today:
            # Future event → ensure it's Upcoming
            if event['status'] not in ('Upcoming', 'Cancelled'):
                cursor.execute("""
                    UPDATE events SET status = 'Upcoming'
                    WHERE event_id = ?
                """, (event['event_id'],))

    conn.commit()
    conn.close()


def manual_archive_event(event_id):
    """Manually archive a specific event."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE events SET is_archived = 1 WHERE event_id = ?
    """, (event_id,))
    conn.commit()
    conn.close()


def unarchive_event(event_id):
    """Restore an event from archive."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE events SET is_archived = 0 WHERE event_id = ?
    """, (event_id,))
    conn.commit()
    conn.close()
