# py-exif-time

Parse and normalize EXIF date-time strings from image metadata into one
canonical form.

```python
from py_exif_time import parse_exif_datetime, normalize_exif_datetime

record = parse_exif_datetime("2023:07:14 09:05:06.123")
print(record.year, record.month, record.day)   # 2023 7 14
print(record.millisecond)                      # 123
print(record.isoformat())                      # 2023-07-14T09:05:06.123

print(normalize_exif_datetime("2023-07-14T09:05:06.25"))
# 2023:07:14 09:05:06.250
```

The package exports three names:

- `parse_exif_datetime(value)` returns an `ExifDateTime` dataclass.
- `normalize_exif_datetime(value)` returns the canonical string.
- `ExifDateTime` is the frozen dataclass with fields `year`, `month`,
  `day`, `hour`, `minute`, `second`, `millisecond`, plus the methods
  `isoformat()` and `normalized()`.

## Why this exists

EXIF stores the primary timestamp as `YYYY:MM:DD HH:MM:SS`, but the
subsecond part is not part of that field — it lives in a separate
`SubSecTime` tag, and many writers instead glue it onto the main string
with `.`, `,` or even `:`. Re-writing metadata with a generic tool often
produces the ISO 8601 spelling instead. Callers who only need to sort or
compare timestamps end up writing the same regex in every project.

The trade-off here is that we normalize to a single spelling with a
fixed three-digit millisecond component, rather than preserving the
original text. That loses the distinction between "no subsecond data"
and "subsecond data of exactly zero", but it makes the output a plain
sortable string and removes the branching from downstream code.

## The awkward edge

Fractional seconds are truncated, not rounded. `...06.9999` becomes
`...06.999`, not `...07.000`. Rounding would roll the second forward and
can change the date on a year boundary, so truncation is the safer
choice for a value that is only ever a hint about when the shutter
fired. Leap seconds (`:60`) are accepted as-is; they are not normalized
away.

Calendar validation is deliberately shallow: month and day ranges are
checked, and 30-day months and February are checked against 30 and 29
respectively, but full leap-year rules are not applied. A camera that
emits `2023:02:29` will parse successfully.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

