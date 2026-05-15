
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import dateparser
from dateparser.search import search_dates

from ..config import Config

_SETTINGS = {
  'PREFER_DATES_FROM': 'future',
  'RETURN_AS_TIMEZONE_AWARE': True,
  'TO_TIMEZONE': 'UTC',
  'TIMEZONE': Config().timezone
}

def _get_timezone() -> ZoneInfo:
  timezone_name = Config().timezone
  try:
    return ZoneInfo(timezone_name)
  except ZoneInfoNotFoundError:
    return ZoneInfo('UTC')

def _parse_datetime_input(text: str) -> datetime:
  if not text or not text.strip():
    raise ValueError('Datetime expression is required')

  parsed = dateparser.parse(text, settings=_SETTINGS)
  if parsed is None:
    fallback = search_dates(text, settings=_SETTINGS)
    if fallback:
      parsed = fallback[0][1]
    else:
      raise ValueError(f'Unable to parse datetime: {text}')

  return parsed

def str_to_datetime(value: str | None) -> datetime | None:
  if value is None:
    return None
  parsed = datetime.fromisoformat(value)
  if parsed.tzinfo is None:
    return parsed.replace(tzinfo=UTC)
  return parsed.astimezone(UTC)

def ensure_utc(value: datetime | None) -> datetime | None:
  if value is None:
    return None
  if value.tzinfo is None:
    return value.replace(tzinfo=UTC)
  return value.astimezone(UTC)

def coerce_datetime(value: datetime | str | None) -> datetime | None:
  if value is None:
    return None
  if isinstance(value, datetime):
    return ensure_utc(value)
  return _parse_datetime_input(value)

def format_datetime(value: str | None) -> str:
  parsed = str_to_datetime(value)
  if parsed is None:
    return 'None'

  timezone = _get_timezone()
  local = parsed.astimezone(timezone)
  label = timezone.key if hasattr(timezone, 'key') else str(timezone)
  return f"{local.strftime('%Y-%m-%d %H:%M')} ({label})"

def get_day_bounds(value: datetime) -> tuple[datetime, datetime]:
  timezone = _get_timezone()
  local = value if value.tzinfo is not None else value.replace(tzinfo=timezone)
  local = local.astimezone(timezone)
  day_start = local.replace(hour=0, minute=0, second=0, microsecond=0)
  day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
  return day_start.astimezone(UTC), day_end.astimezone(UTC)

def get_today_bounds() -> tuple[datetime, datetime]:
  timezone = _get_timezone()
  return get_day_bounds(datetime.now(timezone))
