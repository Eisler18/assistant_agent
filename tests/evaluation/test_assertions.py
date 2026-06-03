from types import SimpleNamespace
from langchain_core.messages import AIMessage, HumanMessage

from evaluation import assertions

# pylint: disable=too-few-public-methods
class DummyRepo:
  def __init__(self, tasks):
    self._tasks = tasks

  def list(self, _query=None):
    return self._tasks
# pylint: enable=too-few-public-methods

def _task(**overrides):
  base = {
    'id': 'task-1',
    'title': 'Task A',
    'status': 'pending',
    'deadline': '2026-05-24T10:00:00+00:00'
  }
  return {**base, **overrides}

def test_assert_repository_task_exists():
  repo = DummyRepo([_task(title='Task A')])
  result = assertions.assert_repository_task_exists(repo, 'title', 'Task A')
  assert result.passed is True

  repo = DummyRepo([_task(title='Task B')])
  result = assertions.assert_repository_task_exists(repo, 'title', 'Task A')
  assert result.passed is False
  assert 'No task found' in result.detail

def test_assert_repository_task_absent():
  repo = DummyRepo([_task(title='Task A')])
  result = assertions.assert_repository_task_absent(repo, 'title', 'Task B')
  assert result.passed is True

  result = assertions.assert_repository_task_absent(repo, 'title', 'Task A')
  assert result.passed is False
  assert 'Unexpected task found' in result.detail

def test_assert_repository_count_delta():
  repo = DummyRepo([_task(), _task(id='task-2')])
  result = assertions.assert_repository_count_delta(repo, 1, 1)
  assert result.passed is True

  result = assertions.assert_repository_count_delta(repo, 1, 2)
  assert result.passed is False
  assert 'Expected count' in result.detail

def test_assert_task_field_equals():
  repo = DummyRepo([_task(status='completed')])
  result = assertions.assert_task_field_equals(repo, 'Task A', 'status', 'completed')
  assert result.passed is True

  result = assertions.assert_task_field_equals(repo, 'Task A', 'status', 'pending')
  assert result.passed is False
  assert 'Expected status' in result.detail

  result = assertions.assert_task_field_equals(repo, 'Missing', 'status', 'pending')
  assert result.passed is False
  assert 'not found' in result.detail

def test_assert_task_field_date_within():
  repo = DummyRepo([_task(deadline='2026-05-24T10:00:00+00:00')])
  result = assertions.assert_task_field_date_within(
    repo,
    'Task A',
    'deadline',
    '2026-05-24T10:00:00+00:00',
    1
  )
  assert result.passed is True

  result = assertions.assert_task_field_date_within(
    repo,
    'Task A',
    'deadline',
    '2026-05-24T12:00:00+00:00',
    1
  )
  assert result.passed is False
  assert 'Datetime outside tolerance' in result.detail

def test_assert_tools_called_include():
  result = assertions.assert_tools_called_include(['a', 'b'], ['a'])
  assert result.passed is True

  result = assertions.assert_tools_called_include(['a'], ['a', 'c'])
  assert result.passed is False
  assert 'Missing tools' in result.detail

def test_assert_tools_not_called():
  result = assertions.assert_tools_not_called(['a', 'b'], ['c'])
  assert result.passed is True

  result = assertions.assert_tools_not_called(['a', 'b'], ['b'])
  assert result.passed is False
  assert 'Unexpected tools' in result.detail

def test_assert_tool_call_order():
  result = assertions.assert_tool_call_order(['a', 'b', 'c'], 'a', 'c')
  assert result.passed is True

  result = assertions.assert_tool_call_order(['a', 'b', 'c'], 'c', 'a')
  assert result.passed is False

  result = assertions.assert_tool_call_order(['a', 'b'], 'a', 'x')
  assert result.passed is False
  assert 'Missing tools' in result.detail

def test_assert_interrupt_fired():
  result = assertions.assert_interrupt_fired(SimpleNamespace(interrupts=['stop']))
  assert result.passed is True

  result = assertions.assert_interrupt_fired(SimpleNamespace(interrupts=[]))
  assert result.passed is False

def test_assert_task_not_saved_before_interrupt():
  result = assertions.assert_task_not_saved_before_interrupt(3, 3)
  assert result.passed is True

  result = assertions.assert_task_not_saved_before_interrupt(2, 3)
  assert result.passed is False
  assert 'Expected 3' in result.detail

  result = assertions.assert_task_not_saved_before_interrupt(None, 3)
  assert result.passed is False
  assert 'not reached' in result.detail

def test_assert_calendar_link_in_response():
  messages = [
    HumanMessage(content='User'),
    AIMessage(content='link calendar.google.com')
  ]
  result = assertions.assert_calendar_link_in_response(messages)
  assert result.passed is True

  result = assertions.assert_calendar_link_in_response([HumanMessage(content='User')])
  assert result.passed is False
