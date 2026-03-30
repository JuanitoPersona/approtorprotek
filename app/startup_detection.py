from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

from .models import SINGLE_START_REQUIRED_HEADERS


DateTuple = Tuple[int, int, int, int, int, int]
MultiStartRow = Tuple[DateTuple, str, Sequence[str]]


def normalize_header(value) -> str:
    return "".join(ch for ch in str(value).strip().lower() if ch.isalnum() or ch in "()%")


def decode_datetime(a, b, c) -> DateTuple:
    def parts(raw):
        try:
            value = int(raw)
        except Exception:
            value = 0
        return (value >> 8) & 0xFF, value & 0xFF

    year, month = parts(a)
    day, hour = parts(b)
    minute, second = parts(c)
    return 2000 + year, month, day, hour, minute, second


def format_datetime(dt: DateTuple) -> str:
    year, month, day, hour, minute, second = dt
    return f"{year:04d}/{month:02d}/{day:02d} {hour:02d}:{minute:02d}:{second:02d}"


def is_valid_datetime(dt: DateTuple) -> bool:
    year, month, day, hour, minute, second = dt
    return 2000 <= year <= 2099 and 1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60


def extract_multi_start_rows(rows: Iterable[Sequence[str]]) -> List[MultiStartRow]:
    items: List[MultiStartRow] = []
    for row in rows:
        if len(row) < 5:
            continue
        dt = decode_datetime(row[2], row[3], row[4])
        if not is_valid_datetime(dt):
            continue
        if not any(str(cell).strip().upper() != "3FFF" for cell in row):
            continue
        items.append((dt, format_datetime(dt), row))
    items.sort(key=lambda item: item[0])
    return items


def detect_csv_type(rows: Sequence[Sequence[str]]) -> Optional[str]:
    if not rows:
        return None

    header_tokens = {normalize_header(value) for value in rows[0] if str(value).strip()}
    if SINGLE_START_REQUIRED_HEADERS.issubset(header_tokens):
        return "single_file"

    if extract_multi_start_rows(rows):
        return "multi_file"
    return None
