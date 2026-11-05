"""Core parsing for EXIF date-time strings.

The EXIF specification defines the primary timestamp as
``YYYY:MM:DD HH:MM:SS`` (note the colon between date and time components,
which differs from ISO 8601). Subsecond information, when present, is
stored in a separate ``SubSecTime`` tag as a decimal fraction. Some
writers instead append the fraction to the main timestamp with a dot or
comma.

This module accepts all of those spellings and returns a single
:class:`ExifDateTime` value. The design choice is to normalize to a
space-separated form with a fixed millisecond component, because that is
what most downstream consumers (loggers, file renamers, JSON encoders)
want, and because it keeps the output sortable as a plain string.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

__all__ = ["ExifDateTime", "parse_exif_datetime", "normalize_exif_datetime"]


# Primary layout: "YYYY:MM:DD HH:MM:SS" with optional fraction attached
# by '.', ',' or ':' (the colon form appears in some scanner output).
_PRIMARY_RE = re.compile(
    r"^\s*"
    r"(?P<year>\d{4}):(?P<month>\d{2}):(?P<day>\d{2})"
    r"[ T]"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
    r"(?:[.,:](?P<fraction>\d+))?"
    r"\s*$"
)

# Secondary layout: ISO 8601 style, accepted for convenience because
# many tools emit it when re-writing metadata.
_ISO_RE = re.compile(
    r"^\s*"
    r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
    r"[ T]"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
    r"(?:[.,](?P<fraction>\d+))?"
    r"\s*$"
)


@dataclass(frozen=True)
class ExifDateTime:
    """A parsed EXIF timestamp.

    ``millisecond`` is always in ``[0, 999]``. The original fraction is
    truncated rather than rounded so that a value like ``.9999`` becomes
    ``999`` and never rolls the second forward.
    """

    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    millisecond: int = 0

    def isoformat(self) -> str:
        """Return an ISO 8601-ish string with millisecond precision."""
        return (
            f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
            f"T{self.hour:02d}:{self.minute:02d}:{self.second:02d}"
            f".{self.millisecond:03d}"
        )

    def normalized(self) -> str:
        """Return the canonical form used by :func:`normalize_exif_datetime`.

        The separator is a space, not ``T``, to match the EXIF spelling
        while still keeping the string lexicographically sortable.
        """
        return (
            f"{self.year:04d}:{self.month:02d}:{self.day:02d} "
            f"{self.hour:02d}:{self.minute:02d}:{self.second:02d}."
            f"{self.millisecond:03d}"
        )


def _is_valid(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
) -> bool:
    """Check field ranges without importing ``datetime``.

    Using ``datetime`` would pull in timezone and calendar machinery we
    do not need, and would reject the leap-second value 60 that some
    cameras emit. We accept 60 for seconds and document it.
    """
    if not (0 <= year <= 9999):
        return False
    if not (1 <= month <= 12):
        return False
    if not (1 <= day <= 31):
        return False
    if not (0 <= hour <= 23):
        return False
    if not (0 <= minute <= 59):
        return False
    if not (0 <= second <= 60):
        return False
    # Reject obviously impossible day/month pairs. Full calendar
    # validation is out of scope; this catches typos like month 02 day 30.
    if month in (4, 6, 9, 11) and day > 30:
        return False
    if month == 2 and day > 29:
        return False
    return True


def _fraction_to_millis(fraction: Optional[str]) -> int:
    """Convert a fractional-second string to milliseconds by truncation."""
    if not fraction:
        return 0
    # Pad or trim to three digits. Truncation avoids rounding up into the
    # next second, which would change the date on a boundary.
    digits = (fraction + "000")[:3]
    return int(digits)


def parse_exif_datetime(value: str) -> ExifDateTime:
    """Parse an EXIF or ISO-style date-time string.

    Raises :class:`ValueError` if the string does not match a known layout
    or has out-of-range fields. The accepted layouts are:

    * ``YYYY:MM:DD HH:MM:SS``
    * ``YYYY:MM:DD HH:MM:SS.fff``
    * ``YYYY:MM:DD HH:MM:SS,fff``
    * ``YYYY:MM:DD HH:MM:SS:fff``
    * ``YYYY-MM-DD HH:MM:SS`` and ``YYYY-MM-DDTHH:MM:SS`` with the same
      optional fractional suffixes.
    """
    if not isinstance(value, str):
        raise TypeError("value must be a string")

    match = _PRIMARY_RE.match(value)
    if match is None:
        match = _ISO_RE.match(value)
    if match is None:
        raise ValueError(f"unrecognized EXIF date-time: {value!r}")

    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second"))
    millisecond = _fraction_to_millis(match.group("fraction"))

    if not _is_valid(year, month, day, hour, minute, second):
        raise ValueError(f"out-of-range EXIF date-time: {value!r}")

    return ExifDateTime(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        millisecond=millisecond,
    )


def normalize_exif_datetime(value: str) -> str:
    """Parse ``value`` and return its canonical string form.

    The canonical form is ``YYYY:MM:DD HH:MM:SS.mmm``. Missing fractions
    become ``.000``. This is the function most callers want.
    """
    return parse_exif_datetime(value).normalized()
