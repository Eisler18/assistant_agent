
from datetime import datetime, UTC
from zoneinfo import ZoneInfo
from unittest.mock import patch
import pytest
from assistant_agent.utils.date_parser import parse_date

# ------------------------------------------------------------------ #
# Helpers                                                            #
# ------------------------------------------------------------------ #
@pytest.fixture(autouse=True)
def set_utc_timezone():
  with patch('assistant_agent.utils.date_parser._SETTINGS', {
    'PREFER_DATES_FROM': 'future',
    'RETURN_AS_TIMEZONE_AWARE': True,
    'TO_TIMEZONE': 'UTC',
    'TIMEZONE': 'UTC'
  }):
    yield

# ------------------------------------------------------------------ #
# Configuration                                                      #
# ------------------------------------------------------------------ #
class TestTimezoneConfiguration:
  def test_default_timezone_is_utc_when_env_not_set(self):
    result = parse_date('2026-06-15 12:00')
    assert result.hour == 12
    assert result.utcoffset().total_seconds() == 0

  def test_custom_timezone_is_applied(self):
    timezone = 'Europe/Madrid'
    with patch('assistant_agent.utils.date_parser._SETTINGS', {
      'PREFER_DATES_FROM': 'future',
      'RETURN_AS_TIMEZONE_AWARE': True,
      'TO_TIMEZONE': 'UTC',
      'TIMEZONE': timezone
    }):
      result = parse_date('2026-06-15 12:00')
      expected_result = datetime(2026, 6, 15, 12, 0, tzinfo=ZoneInfo(timezone)).astimezone(UTC)
      assert result.hour == expected_result.hour
      assert result.utcoffset().total_seconds() == 0

# ------------------------------------------------------------------ #
# Result type                                                            #
# ------------------------------------------------------------------ #
class TestParseDateResultType:
  def test_returns_datetime(self):
    result = parse_date('tomorrow')
    assert isinstance(result, datetime)
    assert result.utcoffset().total_seconds() == 0

  def test_empty_string_returns_none(self):
    assert parse_date('') is None

  def test_whitespace_only_returns_none(self):
    assert parse_date('   ') is None

  def test_unrecognisable_input_returns_none(self):
    assert parse_date('not a date at all') is None


# ------------------------------------------------------------------ #
# Absolute dates                                                      #
# ------------------------------------------------------------------ #
class TestAbsoluteDates:
  def test_parses_full_date(self):
    result = parse_date('June 15 2026')
    assert result.year == 2026
    assert result.month == 6
    assert result.day == 15

  def test_parses_iso_format(self):
    result = parse_date('2026-06-15')
    assert result.year == 2026
    assert result.month == 6
    assert result.day == 15

  def test_parses_date_with_time(self):
    result = parse_date('June 15 2026 at 5pm')
    assert result.year == 2026
    assert result.month == 6
    assert result.day == 15
    assert result.hour == 17

# ------------------------------------------------------------------ #
# Relative dates (frozen clock)                                       #
# ------------------------------------------------------------------ #

class TestRelativeDates:
  def test_in_n_days(self):
    result = parse_date('in 3 days')
    assert round((result - datetime.now(UTC)).total_seconds() / (24 * 3600)) == 3

  def test_next_week(self):
    result = parse_date('next week')
    assert round((result - datetime.now(UTC)).total_seconds() / (24 * 3600)) == 7

  def test_parses_weekday_dates(self):
    result = parse_date('Monday at 9am')
    assert result.weekday() == 0
    assert result.hour == 9

  def test_parses_months(self):
    result = parse_date('in 2 months at 3pm')
    assert round((result - datetime.now(UTC)).total_seconds() / (30 * 24 * 3600)) == 2
    assert result.hour == 15
