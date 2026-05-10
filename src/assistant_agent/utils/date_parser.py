
from datetime import datetime
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
