
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
import pytest
from assistant_agent import utils
from assistant_agent.graph import tools

class DummyTask:
  def __init__(self, data):
    self._data = data
    self.id = data.get('id')
    self.title = data.get('title')
    self.status = data.get('status')

  def to_dict(self):
    return self._data

  def update(self, **kwargs):
    updated = {**self._data, **kwargs}
    return DummyTask(updated)

  def delete(self):
    deleted = {**self._data, 'status': 'deleted'}
    return DummyTask(deleted)

@pytest.fixture(autouse=True)
def set_utc_timezone(monkeypatch):
  monkeypatch.setattr(
    utils.date_parser,
    '_SETTINGS',
    { **utils.date_parser._SETTINGS, 'TIMEZONE': 'UTC' } # pylint: disable=protected-access
  )
  monkeypatch.setattr(utils.date_parser, '_get_timezone', lambda: utils.date_parser.ZoneInfo('UTC'))

# ------------------------------------------------------------------ #
# Generic Tool tests                                                 #
# ------------------------------------------------------------------ #
def test_tools_have_descriptions():
  tool_list = [
    tools.create_task,
    tools.get_task,
    tools.delete_task,
    tools.parse_date_range,
    tools.update_task,
    tools.build_overdue_filter,
    tools.list_tasks,
    tools.format_task_preview
  ]

  for tool in tool_list:
    assert tool.description


# ------------------------------------------------------------------ #
# Time-related Tool tests                                            #
# ------------------------------------------------------------------ #
def test_parse_date_range_tool():
  parsed_range = tools.parse_date_range.invoke({
    'expression': 'this Monday',
    'end_expression': 'this Friday'
  })
  assert isinstance(parsed_range, dict)
  assert { 'start_time', 'end_time' }.issubset(parsed_range.keys())
  assert parsed_range['start_time'] < parsed_range['end_time']
  assert parsed_range['start_time'].weekday() == 0
  assert parsed_range['end_time'].weekday() == 4

  parsed_range = tools.parse_date_range.invoke({
    'expression': 'this week'
  })
  assert parsed_range['start_time'].weekday() == 0
  assert parsed_range['end_time'].weekday() == 6
  assert parsed_range['end_time'] - parsed_range['start_time'] == timedelta(days=6)

  parsed_range = tools.parse_date_range.invoke({
    'expression': 'this month'
  })
  assert parsed_range['start_time'].day == 1
  assert parsed_range['end_time'].day >= 28 and parsed_range['end_time'].day <= 31
  assert parsed_range['start_time'].month == datetime.now(tools.UTC).month
  assert parsed_range['start_time'].month == parsed_range['end_time'].month

  parsed_range = tools.parse_date_range.invoke({
    'expression': '2026-05-01'
  })
  assert parsed_range['start_time'].day == 1
  assert parsed_range['start_time'].month == 5
  assert parsed_range['start_time'].year == 2026
  assert parsed_range['end_time'] - parsed_range['start_time'] == timedelta(days=1, microseconds=-1)

def test_build_overdue_filter_tool():
  overdue = tools.build_overdue_filter.invoke({})
  assert isinstance(overdue, dict)
  assert { 'deadline_lte', 'status' }.issubset(overdue.keys())
  assert isinstance(overdue['deadline_lte'], datetime)
  assert overdue['status'] == 'pending'
  now = datetime.now(tools.UTC)
  delta = abs((overdue['deadline_lte'] - now).total_seconds())
  assert delta <= 5

def test_build_today_filter_tool():
  today = tools.build_today_filter.invoke({})
  assert isinstance(today, dict)
  assert { 'planned_at_gte', 'planned_at_lte' }.issubset(today.keys())
  assert isinstance(today['planned_at_gte'], datetime)
  assert today['planned_at_gte'] < today['planned_at_lte']
  assert today['planned_at_gte'].hour == 0
  assert today['planned_at_lte'].hour == 23

def test_build_unscheduled_filter_tool():
  unscheduled = tools.build_unscheduled_filter.invoke({})
  assert isinstance(unscheduled, dict)
  assert { 'has_deadline', 'has_planned_at' }.issubset(unscheduled.keys())
  assert unscheduled['has_deadline'] is True
  assert unscheduled['has_planned_at'] is False

# ------------------------------------------------------------------- #
# Task-related Tool tests                                             #
# ------------------------------------------------------------------- #
def test_initialize_task_tool(monkeypatch):
  initialized = tools.new_task.invoke({
    'title': 'Write intro',
    'description': 'Draft the introduction section',
    'planned_at': 'tomorrow at 9am',
    'deadline': 'next Monday at 5pm',
    'estimated_minutes': 90
  })['tasks'][0]

  assert initialized['title'] == 'Write intro'
  assert initialized['description'] == 'Draft the introduction section'
  assert initialized['estimated_minutes'] == 90

def test_create_task_tool(monkeypatch):
  created = DummyTask({
    'id': 'task-1',
    'title': 'Write intro',
    'status': 'pending'
  })
  create_mock = MagicMock(return_value=created)
  monkeypatch.setattr(tools.Task, 'save', create_mock)

  result = tools.create_task.invoke({
    'title': 'Write intro',
    'planned_at': 'tomorrow at 9am',
    'deadline': 'next Monday at 5pm',
    'estimated_minutes': 90
  })

  assert result == { 'tasks': [created.to_dict()] }

def test_get_task_tool(monkeypatch):
  found = DummyTask({
    'id': 'task-2',
    'title': 'Read notes',
    'status': 'pending'
  })
  find_mock = MagicMock(return_value=found)
  monkeypatch.setattr(tools.Task, 'find', find_mock)

  result = tools.get_task.invoke({'task_id': 'task-2'})
  assert result == { 'tasks': [found.to_dict()] }

  def _raise(_):
    raise KeyError('not found')

  monkeypatch.setattr(tools.Task, 'find', _raise)

  with pytest.raises(ValueError, match='not found'):
    tools.get_task.invoke({'task_id': 'missing'})

def test_list_tasks_tool(monkeypatch):
  results = [
    DummyTask({
      'id': 'task-3',
      'title': 'Plan',
      'status': 'pending',
      'planned_at': '2026-05-01T10:00:00+00:00',
      'deadline': '2026-05-02T10:00:00+00:00'
    })
  ]
  search_mock = MagicMock(return_value=results)
  monkeypatch.setattr(tools.Task, 'search', search_mock)

  output = tools.list_tasks.invoke({
    'status': 'pending',
    'planned_at_gte': '2026-05-01 08:00',
    'planned_at_lte': '2026-05-01 18:00',
    'deadline_lte': '2026-05-01 18:00',
    'has_deadline': True,
    'has_planned_at': True
  })

  assert output == { 'tasks': [results[0].to_dict()] }
  query = search_mock.call_args.args[0]
  assert query['status'] == 'pending'
  assert isinstance(query['planned_at_gte'], datetime)

  search_mock = MagicMock(return_value=[])
  monkeypatch.setattr(tools.Task, 'search', search_mock)

  output = tools.list_tasks.invoke({})
  assert output == 'No tasks found matching the filters.'

def test_update_task_tool(monkeypatch):
  task = DummyTask({
    'id': 'task-4',
    'title': 'Draft',
    'status': 'pending'
  })
  find_mock = MagicMock(return_value=task)
  monkeypatch.setattr(tools.Task, 'find', find_mock)

  result = tools.update_task.invoke({
    'task_id': 'task-4',
    'status': 'completed',
    'planned_at': '2026-05-01 10:00',
    'estimated_minutes': 120,
    'description': 'Write the first draft',
    'deadline': '2026-05-02 10:00',
    'title': 'Reviewed Draft'
  })['tasks'][0]

  assert result['status'] == 'completed'
  assert result['title'] == 'Reviewed Draft'
  assert result['description'] == 'Write the first draft'
  assert result['estimated_minutes'] == 120
  assert result['planned_at'] == datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
  assert result['deadline'] == datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
  assert result['id'] == 'task-4'

def test_delete_task_tool(monkeypatch):
  task = DummyTask({
    'id': 'task-5',
    'title': 'Remove',
    'status': 'pending'
  })
  find_mock = MagicMock(return_value=task)
  monkeypatch.setattr(tools.Task, 'find', find_mock)

  result = tools.delete_task.invoke({'task_id': 'task-5'})['tasks'][0]
  assert result['status'] == 'deleted'

def test_format_task_preview_excludes_internal_fields():
  preview = tools.format_task_preview.invoke({ 'tasks': [{
    'id': '1b206596-c446-4634-b567-f9383c6967ec',
    'title': 'Preview',
    'planned_at': '2026-05-10T10:00:00+00:00',
    'deadline': '2026-05-11T10:00:00+00:00',
    'estimated_minutes': 60,
    'status': 'pending',
    'created_at': '2026-05-01T10:00:00+00:00',
    'updated_at': '2026-05-02T10:00:00+00:00',
    'completed_at': None
  }] })

  assert 'internal-id' not in preview
  assert 'created_at' not in preview
  assert 'updated_at' not in preview
  assert 'completed_at' not in preview
  assert 'Preview' in preview

  preview = tools.format_task_preview.invoke({ 'tasks': [] })
  assert preview == 'No tasks found.'
