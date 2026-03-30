
from datetime import UTC, datetime, timezone
from uuid import uuid4

import pytest

from assistant_agent.models.task import Task, TaskStatus

# ------------------------------------------------------------------ #
# TaskStatus                                                         #
# ------------------------------------------------------------------ #
class TestTaskStatus:
  def test_values_are_strings(self):
    '''TaskStatus inherits from str — values must be plain strings.'''
    assert TaskStatus.PENDING == 'pending'
    assert TaskStatus.COMPLETED == 'completed'
    assert TaskStatus.DELETED == 'deleted'

  def test_is_str_subclass(self):
    assert isinstance(TaskStatus.PENDING, str)

# ------------------------------------------------------------------ #
# Task Validators                                                    #
# ------------------------------------------------------------------ #
class TestTitleValidator:
  def test_rejects_empty_string(self):
    with pytest.raises(ValueError, match='title must not be empty'):
      Task.create(title='')

  def test_rejects_whitespace_only(self):
    with pytest.raises(ValueError, match='title must not be empty'):
      Task.create(title='   ')

  def test_strips_surrounding_whitespace(self):
    task = Task.create(title='  Write thesis  ')
    assert task.title == 'Write thesis'

  def test_accepts_valid_title(self):
    task = Task.create(title='Write thesis chapter')
    assert task.title == 'Write thesis chapter'

class TestEstimatedMinutesValidator:
  @pytest.mark.parametrize('input_val, expected', [
      (15, 15),
      (16, 30),
      (1, 15),
      (29, 30)
  ])

  def test_rounds_up_to_nearest_15(self, input_val, expected):
    task = Task.create(title='Task', estimated_minutes=input_val)
    assert task.estimated_minutes == expected

  def test_rejects_zero(self):
    with pytest.raises(ValueError, match='must be a positive integer'):
      Task.create(title='Task', estimated_minutes=0)

  def test_rejects_negative(self):
    with pytest.raises(ValueError, match='must be a positive integer'):
      Task.create(title='Task', estimated_minutes=-15)

  def test_accepts_none(self):
    task = Task.create(title='Task', estimated_minutes=None)
    assert task.estimated_minutes is None

  def test_none_by_default(self):
    task = Task.create(title='Task')
    assert task.estimated_minutes is None

# ------------------------------------------------------------------ #
# Task Callbacks                                                     #
# ------------------------------------------------------------------ #
class TestCompletedAtConsistency:
  def test_auto_sets_completed_at_on_completed_status(self):
    task = Task.create(title='Task', status=TaskStatus.COMPLETED)
    assert task.completed_at is not None

  def test_clears_completed_at_on_non_completed_status(self):
    task = Task.create(title='Task', status=TaskStatus.COMPLETED)
    assert task.completed_at is not None

    task = task.update(status=TaskStatus.PENDING)
    assert task.completed_at is None

# ------------------------------------------------------------------- #
# Public Interface                                                   #
# ------------------------------------------------------------------- #
class TestTaskCreate:
  def test_creates_task_with_given_fields(self):
    task = Task.create(
      title=' Write thesis',
      description='Finish writing the thesis by the end of the month.',
      deadline=datetime(2024, 6, 30).date(),
      planned_date=datetime(2024, 6, 29).date(),
      estimated_minutes=115
    )
    assert task.title == 'Write thesis'
    assert task.description == 'Finish writing the thesis by the end of the month.'
    assert task.deadline == datetime(2024, 6, 30).date()
    assert task.planned_date == datetime(2024, 6, 29).date()
    assert task.estimated_minutes == 120
    assert task.status == TaskStatus.PENDING
    assert task.created_at is not None
    assert task.updated_at is not None
    assert task.id is not None

class TestTaskUpdate:
  def test_updates_given_fields(self):
    task = Task.create(
      title='Task',
      description='Desc',
      estimated_minutes=20,
      updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
    )
    updated = task.update(title='New Task', estimated_minutes=35)

    assert updated.title == 'New Task'
    assert updated.description == 'Desc'
    assert updated.estimated_minutes == 45
    assert updated.updated_at > task.updated_at

  def test_ignores_immutable_fields(self):
    task = Task.create(title='Task')
    updated = task.update(id=uuid4(), created_at=datetime(2000, 1, 1, tzinfo=timezone.utc))

    assert updated.id == task.id
    assert updated.created_at == task.created_at

  def test_rejects_unknown_fields(self):
    task = Task.create(title='Task')
    with pytest.raises(ValueError, match='Unknown fields: foo, bar'):
      task.update(foo=123, bar='abc')

# ------------------------------------------------------------------- #
# Serialization                                                       #
# ------------------------------------------------------------------- #
class TestTaskSerialization:
  def test_serializes_to_dict(self):
    task = Task.create(title='Task', description='Desc', estimated_minutes=20)
    data = task.to_dict()
    assert data['title'] == 'Task'
    assert data['description'] == 'Desc'
    assert data['estimated_minutes'] == 30
    assert 'id' in data
    assert 'created_at' in data
    assert 'updated_at' in data

  def test_serialized_dict_to_instance(self):
    data = {
      'id': str(uuid4()),
      'title': 'Task',
      'description': 'Desc',
      'estimated_minutes': 30,
      'created_at': datetime.now(UTC).isoformat(),
      'updated_at': datetime.now(UTC).isoformat(),
    }
    task = Task.from_dict(data)
    assert task.title == 'Task'
    assert task.description == 'Desc'
    assert task.estimated_minutes == 30
    assert str(task.id) == data['id']
    assert task.created_at.isoformat() == data['created_at']
    assert task.updated_at.isoformat() == data['updated_at']