
from datetime import datetime, UTC
from zoneinfo import ZoneInfo
from unittest.mock import patch
import pytest
from assistant_agent.utils.date_parser import (
  coerce_datetime,
  ensure_utc,
  format_datetime,
  get_day_bounds,
  get_today_bounds,
  str_to_datetime
)

# ------------------------------------------------------------------ #
# Helpers                                                            #
# ------------------------------------------------------------------ #
@pytest.fixture(autouse=True)
def set_utc_timezone(monkeypatch):
  monkeypatch.setenv('AGENT_TIMEZONE', 'UTC')
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
    result = coerce_datetime('2026-06-15 12:00')
    assert result.hour == 12
    assert result.utcoffset().total_seconds() == 0

  def test_custom_timezone_is_applied(self):
    timezone = 'Europe/Madrid'
    with patch('assistant_agent.utils.date_parser._SETTINGS', {
      'PREFER_DATES_FROM': 'future',
      'RETURN_AS_TIMEZONE_AWARE': True,
      'TO_TIMEZONE': 'UTC',
      'TIMEZONE': timezone
    }), patch('assistant_agent.config.os.getenv', return_value=timezone):
      result = coerce_datetime('2026-06-15 12:00')
      expected_result = datetime(2026, 6, 15, 12, 0, tzinfo=ZoneInfo(timezone)).astimezone(UTC)
      assert result.hour == expected_result.hour
      assert result.utcoffset().total_seconds() == 0

# ------------------------------------------------------------------ #
# Result type                                                            #
# ------------------------------------------------------------------ #
class TestParseDateResultType:
  def test_returns_datetime(self):
    result = coerce_datetime('tomorrow')
    assert isinstance(result, datetime)
    assert result.utcoffset().total_seconds() == 0

  def test_empty_string_returns_none(self):
    with pytest.raises(ValueError, match='Datetime expression is required'):
      coerce_datetime('')

  def test_whitespace_only_returns_none(self):
    with pytest.raises(ValueError, match='Datetime expression is required'):
      coerce_datetime('   ')

  def test_unrecognisable_input_returns_none(self):
    with pytest.raises(ValueError, match='Unable to parse datetime'):
      coerce_datetime('not a date at all')


# ------------------------------------------------------------------ #
# Absolute dates                                                      #
# ------------------------------------------------------------------ #
class TestAbsoluteDates:
  def test_parses_full_date(self):
    result = coerce_datetime('June 15 2026')
    assert result.year == 2026
    assert result.month == 6
    assert result.day == 15

  def test_parses_iso_format(self):
    result = coerce_datetime('2026-06-15')
    assert result.year == 2026
    assert result.month == 6
    assert result.day == 15

  def test_parses_date_with_time(self):
    result = coerce_datetime('June 15 2026 at 5pm')
    assert result.year == 2026
    assert result.month == 6
    assert result.day == 15
    assert result.hour == 17

# ------------------------------------------------------------------ #
# Relative dates (frozen clock)                                       #
# ------------------------------------------------------------------ #
class TestRelativeDates:
  def test_in_n_days(self):
    result = coerce_datetime('in 3 days')
    assert round((result - datetime.now(UTC)).total_seconds() / (24 * 3600)) == 3

  def test_next_week(self):
    result = coerce_datetime('next week')
    assert round((result - datetime.now(UTC)).total_seconds() / (24 * 3600)) == 7

  def test_parses_weekday_dates(self):
    result = coerce_datetime('Monday at 9am')
    assert result.weekday() == 0
    assert result.hour == 9

  def test_parses_months(self):
    result = coerce_datetime('in 2 months at 3pm')
    assert round((result - datetime.now(UTC)).total_seconds() / (30 * 24 * 3600)) == 2
    assert result.hour == 15

# ------------------------------------------------------------------ #
# Task datetime parsing and UTC conversion utilities                 #
# ------------------------------------------------------------------ #
def test_str_to_datetime():
  assert str_to_datetime('2026-06-15T12:00:00') == datetime(
    2026, 6, 15, 12, 0, tzinfo=UTC
  )
  assert str_to_datetime('2026-06-15T12:00:00Z') == datetime(
    2026, 6, 15, 12, 0, tzinfo=UTC
  )
  assert str_to_datetime('2026-06-15T14:00:00+02:00') == datetime(
    2026, 6, 15, 12, 0, tzinfo=UTC
  )
  assert str_to_datetime(None) is None

def test_ensure_utc():
  assert ensure_utc(datetime(2026, 6, 15, 12, 0)) == datetime(
    2026, 6, 15, 12, 0, tzinfo=UTC
  )
  assert ensure_utc(datetime(2026, 6, 15, 12, 0, tzinfo=UTC)) == datetime(
    2026, 6, 15, 12, 0, tzinfo=UTC
  )
  assert ensure_utc(None) is None

def test_coerce_datetime_datetime():
  result = coerce_datetime(datetime(2026, 6, 15, 12, 0))
  assert result.tzinfo == UTC

def test_format_datetime():
  formatted = format_datetime('2026-06-15T12:00:00+00:00')
  assert '2026-06-15 12:00' in formatted
  assert 'UTC' in formatted

  formatted_none = format_datetime(None)
  assert formatted_none == 'None'

def test_get_day_bounds():
  day_start, day_end = get_day_bounds(datetime(2026, 6, 15, 12, 0, tzinfo=UTC))
  assert day_start.tzinfo == UTC
  assert day_end.tzinfo == UTC
  assert day_start.hour == 0
  assert day_end.hour == 23

def test_get_today_bounds():
  day_start, day_end = get_today_bounds()
  assert day_start.tzinfo == UTC
  assert day_end.tzinfo == UTC
  assert day_start.day == datetime.now(UTC).day
  assert day_end.day == datetime.now(UTC).day
