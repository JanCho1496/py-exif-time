"""Parse and normalize EXIF date-time strings.

EXIF stores timestamps in a small number of textual layouts, and the
subsecond field is inconsistent across cameras. This package turns those
strings into a single normalized form so callers do not have to branch on
camera vendor.
"""

from .core import ExifDateTime, parse_exif_datetime, normalize_exif_datetime

__all__ = [
    "ExifDateTime",
    "parse_exif_datetime",
    "normalize_exif_datetime",
]
