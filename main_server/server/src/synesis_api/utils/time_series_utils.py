import pytz
from datetime import datetime, tzinfo
from typing import Literal


def determine_sampling_frequency(timestamps: list[datetime]) -> str:

    if not timestamps or len(timestamps) < 2:
        raise ValueError(
            "At least 2 timestamps are required to determine sampling frequency")

    # Sort timestamps to ensure proper order
    sorted_timestamps = sorted(timestamps)

    # Calculate time differences between consecutive timestamps
    time_diffs = []
    for i in range(1, len(sorted_timestamps)):
        diff = sorted_timestamps[i] - sorted_timestamps[i-1]
        time_diffs.append(diff.total_seconds())

    # Check if all differences are the same (regular sampling)
    if len(set(time_diffs)) == 1:
        # Regular sampling - determine the frequency
        avg_diff_seconds = time_diffs[0]

        # Convert to different time units and find the most appropriate
        if avg_diff_seconds < 60:  # Less than 1 minute
            return "irr"  # Irregular for sub-minute intervals
        elif avg_diff_seconds < 3600:  # Less than 1 hour
            minutes = avg_diff_seconds / 60
            if minutes.is_integer():
                return "m"
            else:
                return "irr"
        elif avg_diff_seconds < 86400:  # Less than 1 day
            hours = avg_diff_seconds / 3600
            if hours.is_integer():
                return "h"
            else:
                return "irr"
        elif avg_diff_seconds < 604800:  # Less than 1 week
            days = avg_diff_seconds / 86400
            if days.is_integer():
                return "d"
            else:
                return "irr"
        elif avg_diff_seconds < 31536000:  # Less than 1 year
            weeks = avg_diff_seconds / 604800
            if weeks.is_integer():
                return "w"
            else:
                return "irr"
        else:  # 1 year or more
            years = avg_diff_seconds / 31536000
            if years.is_integer():
                return "y"
            else:
                return "irr"
    else:
        # Irregular sampling
        return "irr"


def determine_timezone(timestamps: list[datetime]) -> str:

    if not timestamps:
        raise ValueError(
            "At least 1 timestamp is required to determine timezone")

    # Extract timezone info from each timestamp
    timezones = set()
    for ts in timestamps:
        if ts.tzinfo is None:
            # If timestamp is naive, assume UTC
            timezones.add("UTC")
        else:
            # Get timezone name
            tz_name = ts.tzinfo.tzname(ts)
            if tz_name is None:
                # Fallback to timezone offset
                offset = ts.tzinfo.utcoffset(ts)
                if offset is not None:
                    hours = int(offset.total_seconds() / 3600)
                    tz_name = f"UTC{hours:+03d}:00"
                else:
                    tz_name = "UTC"
            timezones.add(tz_name)

    # Check if all timestamps have the same timezone
    if len(timezones) > 1:
        raise ValueError(
            f"Multiple timezones detected in timestamps: {timezones}")

    # Return the single timezone
    return list(timezones)[0]


def timezone_str_to_tz_info(
        timezone_str: Literal[
            "UTC",
            "UTC+00:00",
            "UTC+01:00",
            "UTC+02:00",
            "UTC+03:00",
            "UTC+04:00",
            "UTC+05:00",
            "UTC+06:00",
            "UTC+07:00",
            "UTC+08:00",
            "UTC+09:00",
            "UTC+10:00",
            "UTC+11:00",
            "UTC+12:00",
            "UTC-01:00",
            "UTC-02:00",
            "UTC-03:00",
            "UTC-04:00",
            "UTC-05:00",
            "UTC-06:00",
            "UTC-07:00",
            "UTC-08:00",
            "UTC-09:00",
            "UTC-10:00",
            "UTC-11:00",
            "UTC-12:00",
        ]) -> tzinfo:
    """
    Convert a timezone string to a timezone object.
    """
    return pytz.timezone(timezone_str)


def make_timezone_aware(dt: datetime, timezone_str: str) -> datetime:
    """Convert a naive datetime to timezone-aware using the provided timezone string.

    Args:
        dt: The datetime object to convert (may be naive)
        timezone_str: The timezone string (e.g., 'UTC', 'America/New_York')

    Returns:
        Timezone-aware datetime object
    """
    if dt.tzinfo is not None:
        # Already timezone-aware, return as-is
        return dt

    # Convert naive datetime to timezone-aware
    tz = pytz.timezone(timezone_str)
    return tz.localize(dt)
