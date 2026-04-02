
from datetime import datetime, UTC
import os
import dateparser
from dotenv import load_dotenv

load_dotenv()

_SETTINGS = {
  'PREFER_DATES_FROM': 'future',
  'RETURN_AS_TIMEZONE_AWARE': True,
  'TO_TIMEZONE': 'UTC',
  'TIMEZONE': os.environ.get('AGENT_TIMEZONE', 'UTC')
}

def parse_date(text: str) -> datetime | None:
  if not text or not text.strip():
    return None

  dt = dateparser.parse(text, settings=_SETTINGS)
  if dt is not None and dt.tzinfo is None:
    dt = dt.replace(tzinfo=UTC)

  return dt
