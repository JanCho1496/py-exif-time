"""Tests for py_exif_time.core.

Run with::

    PYTHONPATH=src python -m unittest discover -s tests
"""

import unittest

from py_exif_time import (
    ExifDateTime,
    normalize_exif_datetime,
    parse_exif_datetime,
)


class ParseExifDateTimeTests(unittest.TestCase):
    def test_primary_layout_without_fraction(self):
        got = parse_exif_datetime("2023:07:14 09:05:06")
        self.assertEqual(got, ExifDateTime(2023, 7, 14, 9, 5, 6, 0))

    def test_primary_layout_with_dot_fraction(self):
        got = parse_exif_datetime("2023:07:14 09:05:06.123")
        self.assertEqual(got.millisecond, 123)

    def test_primary_layout_with_comma_fraction(self):
        got = parse_exif_datetime("2023:07:14 09:05:06,5")
        self.assertEqual(got.millisecond, 500)

    def test_primary_layout_with_colon_fraction(self):
        got = parse_exif_datetime("2023:07:14 09:05:06:007")
        self.assertEqual(got.millisecond, 7)

    def test_iso_layout_with_t_separator(self):
        got = parse_exif_datetime("2023-07-14T09:05:06.250")
        self.assertEqual(got, ExifDateTime(2023, 7, 14, 9, 5, 6, 250))

    def test_iso_layout_with_space_separator(self):
        got = parse_exif_datetime("2023-07-14 09:05:06")
        self.assertEqual(got.millisecond, 0)

    def test_fraction_is_truncated_not_rounded(self):
        # A naive round() would turn .9999 into 1000 and roll the second.
        got = parse_exif_datetime("2023:07:14 09:05:06.9999")
        self.assertEqual(got.millisecond, 999)
        self.assertEqual(got.second, 6)

    def test_leap_second_is_accepted(self):
        got = parse_exif_datetime("2016:12:31 23:59:60")
        self.assertEqual(got.second, 60)

    def test_unknown_layout_raises(self):
        with self.assertRaises(ValueError):
            parse_exif_datetime("not a date")

    def test_non_string_raises_type_error(self):
        with self.assertRaises(TypeError):
            parse_exif_datetime(20230714)  # type: ignore[arg-type]

    def test_out_of_range_month_raises(self):
        with self.assertRaises(ValueError):
            parse_exif_datetime("2023:13:01 00:00:00")

    def test_impossible_day_for_month_raises(self):
        with self.assertRaises(ValueError):
            parse_exif_datetime("2023:02:30 00:00:00")

    def test_day_zero_raises(self):
        with self.assertRaises(ValueError):
            parse_exif_datetime("2023:01:00 00:00:00")

    def test_hour_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            parse_exif_datetime("2023:01:01 24:00:00")

    def test_surrounding_whitespace_is_tolerated(self):
        got = parse_exif_datetime("  2023:07:14 09:05:06  ")
        self.assertEqual(got.year, 2023)


class NormalizeExifDateTimeTests(unittest.TestCase):
    def test_missing_fraction_becomes_zero_millis(self):
        self.assertEqual(
            normalize_exif_datetime("2023:07:14 09:05:06"),
            "2023:07:14 09:05:06.000",
        )

    def test_iso_input_is_rewritten_to_exif_form(self):
        self.assertEqual(
            normalize_exif_datetime("2023-07-14T09:05:06.25"),
            "2023:07:14 09:05:06.250",
        )

    def test_normalized_string_sorts_lexicographically(self):
        earlier = normalize_exif_datetime("2023:01:02 03:04:05.006")
        later = normalize_exif_datetime("2023:01:02 03:04:05.060")
        self.assertLess(earlier, later)


class ExifDateTimeMethodsTests(unittest.TestCase):
    def test_isoformat_pads_all_fields(self):
        got = ExifDateTime(2023, 1, 2, 3, 4, 5, 6).isoformat()
        self.assertEqual(got, "2023-01-02T03:04:05.006")

    def test_normalized_matches_module_function(self):
        parsed = parse_exif_datetime("2023:07:14 09:05:06.123")
        self.assertEqual(parsed.normalized(), "2023:07:14 09:05:06.123")

    def test_equality_is_value_based(self):
        self.assertEqual(
            parse_exif_datetime("2023:07:14 09:05:06"),
            parse_exif_datetime("2023-07-14T09:05:06"),
        )


if __name__ == "__main__":
    unittest.main()
