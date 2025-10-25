"""
Utility functions for termnotes
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Get current UTC time as a timezone-naive datetime.

    All timestamps in termnotes are stored as UTC to ensure consistency
    across timezones and avoid comparison issues with timezone-aware datetimes.

    Returns:
        Timezone-naive datetime representing current UTC time
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_to_utc(dt: datetime) -> datetime:
    """
    Normalize a datetime to UTC and remove timezone info.

    If the datetime is timezone-aware, converts it to UTC first.
    If already naive, assumes it's already UTC.

    Args:
        dt: Datetime to normalize

    Returns:
        Timezone-naive datetime in UTC
    """
    if dt.tzinfo is not None:
        # Convert to UTC, then strip timezone
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        # Already naive, assume it's UTC
        return dt
