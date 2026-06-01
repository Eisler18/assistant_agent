from dataclasses import dataclass
from typing import Any

from assistant_agent.utils.date_parser import coerce_datetime

from .trace import get_last_ai_message_content, interrupt_was_fired

@dataclass(frozen=True)
class AssertionResult:
  name: str
  passed: bool
  detail: str = ''

def _format_name(base: str, field: str | None = None) -> str:
  if field:
    return f'{base}:{field}'
  return base

def _find_task(repo, field: str, value: str) -> dict[str, Any] | None:
  for task in repo.list():
    if task.get(field) == value:
      return task
  return None

def assert_repository_task_exists(repo, field: str, value: Any) -> AssertionResult:
  name = _format_name('repository_task_exists', field)
  task = _find_task(repo, field, value)
  if task is not None:
    return AssertionResult(name, True)
  detail = f'No task found with {field}={value!r}.'
  return AssertionResult(name, False, detail)

def assert_repository_task_absent(repo, field: str, value: Any) -> AssertionResult:
  name = _format_name('repository_task_absent', field)
  task = _find_task(repo, field, value)
  if task is None:
    return AssertionResult(name, True)
  detail = f'Unexpected task found with {field}={value!r}.'
  return AssertionResult(name, False, detail)

def assert_repository_count_delta(
  repo,
  initial_count: int | None,
  delta: int
) -> AssertionResult:
  name = 'repository_count_delta'
  if initial_count is None:
    return AssertionResult(name, False, 'Initial count was not provided.')
  expected = initial_count + delta
  actual = len(repo.list())
  passed = actual == expected
  detail = '' if passed else f'Expected count {expected}, got {actual}.'
  return AssertionResult(name, passed, detail)

def assert_task_field_equals(
  repo,
  task_title: str,
  field: str,
  value: Any
) -> AssertionResult:
  name = _format_name('task_field_equals', field)
  task = _find_task(repo, 'title', task_title)
  if task is None:
    detail = f'Task with title {task_title!r} not found.'
    return AssertionResult(name, False, detail)
  actual = task.get(field)
  passed = actual == value
  detail = '' if passed else f'Expected {field}={value!r}, got {actual!r}.'
  return AssertionResult(name, passed, detail)

def assert_task_field_date_within(
  repo,
  task_title: str,
  field: str,
  expression: str,
  tolerance_hours: float
) -> AssertionResult:
  name = _format_name('task_field_date_within', field)
  task = _find_task(repo, 'title', task_title)
  if task is None:
    detail = f'Task with title {task_title!r} not found.'
    return AssertionResult(name, False, detail)

  expected = coerce_datetime(expression)
  actual = coerce_datetime(task.get(field))
  if expected is None or actual is None:
    detail = f'Expected {field} to be a datetime, got {actual!r}.'
    return AssertionResult(name, False, detail)

  delta_hours = abs((actual - expected).total_seconds()) / 3600
  passed = delta_hours <= tolerance_hours
  if passed:
    return AssertionResult(name, True)

  detail = (
    'Datetime outside tolerance. '
    f'expected={expected.isoformat() if expected else "None"}, '
    f'actual={actual.isoformat() if actual else "None"}, '
    f'tolerance_hours={tolerance_hours}, '
    f'delta_hours={delta_hours:.2f}.'
  )
  return AssertionResult(name, False, detail)

def assert_tools_called_include(trace: list[str], tools: list[str]) -> AssertionResult:
  name = 'tools_called_include'
  missing = [tool for tool in tools if tool not in trace]
  if not missing:
    return AssertionResult(name, True)
  detail = f'Missing tools: {", ".join(missing)}.'
  return AssertionResult(name, False, detail)

def assert_tools_not_called(trace: list[str], tools: list[str]) -> AssertionResult:
  name = 'tools_not_called'
  present = [tool for tool in tools if tool in trace]
  if not present:
    return AssertionResult(name, True)
  detail = f'Unexpected tools called: {", ".join(present)}.'
  return AssertionResult(name, False, detail)

def assert_tool_call_order(trace: list[str], before: str, after: str) -> AssertionResult:
  name = 'tool_call_order'
  if before not in trace or after not in trace:
    detail = f'Missing tools in trace. before={before!r}, after={after!r}.'
    return AssertionResult(name, False, detail)
  before_index = trace.index(before)
  after_index = trace.index(after)
  passed = before_index < after_index
  detail = '' if passed else f'Order incorrect: {before_index} !< {after_index}.'
  return AssertionResult(name, passed, detail)

def assert_interrupt_fired(result) -> AssertionResult:
  name = 'interrupt_fired'
  return AssertionResult(name, interrupt_was_fired(result))

def assert_task_not_saved_before_interrupt(
  pre_interrupt_count: int | None,
  initial_count: int | None
) -> AssertionResult:
  name = 'task_not_saved_before_interrupt'
  if pre_interrupt_count is None:
    return AssertionResult(name, False, 'Interrupt turn was not reached.')
  if initial_count is None:
    return AssertionResult(name, False, 'Initial count was not provided.')
  passed = pre_interrupt_count == initial_count
  detail = '' if passed else f'Expected {initial_count}, got {pre_interrupt_count}.'
  return AssertionResult(name, passed, detail)

def assert_calendar_link_in_response(messages: list) -> AssertionResult:
  name = 'calendar_link_in_response'
  content = get_last_ai_message_content(messages)
  passed = 'calendar.google.com' in content
  detail = '' if passed else 'No calendar.google.com link found.'
  return AssertionResult(name, passed, detail)
