
from datetime import UTC, datetime
import dateparser
from assistant_agent.config import Config

_SETTINGS = {
  'PREFER_DATES_FROM': 'future',
  'RETURN_AS_TIMEZONE_AWARE': True,
  'TO_TIMEZONE': 'UTC',
  'TIMEZONE': Config().timezone
}

def parse_date(text: str) -> datetime | None:
  if not text or not text.strip():
    return None

  return dateparser.parse(text, settings=_SETTINGS)

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
