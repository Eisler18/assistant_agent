
from datetime import UTC, datetime, timezone
from uuid import uuid4
import time
from unittest.mock import Mock
import pytest
from assistant_agent.models.task import Task, TaskStatus
from assistant_agent.repository import JsonRepository

# ------------------------------------------------------------------ #
# Fixtures                                                           #
# ------------------------------------------------------------------ #
@pytest.fixture(name='repository')
def mock_repository():
  return Mock(spec=JsonRepository)

@pytest.fixture(autouse=True)
def setup_task_repository(repository):
  Task.set_repository(repository)
  yield
  Task.set_repository(None)

# ------------------------------------------------------------------ #
# Helpers                                                            #
# ------------------------------------------------------------------ #
def create_task(**kwargs) -> Task:
  '''Helper to create a task with default values for testing'''
  defaults = {
    'title': 'Test Task',
    'description': 'A task for testing'
  }
  return Task.create(**{**defaults, **kwargs})

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
# Task Validators/Callbacks                                          #
# ------------------------------------------------------------------ #
class TestTitleValidator:
  def test_rejects_empty_string(self):
    with pytest.raises(ValueError, match='title must not be empty'):
      create_task(title='')

  def test_rejects_whitespace_only(self):
    with pytest.raises(ValueError, match='title must not be empty'):
      create_task(title='   ')

  def test_strips_surrounding_whitespace(self):
    task = create_task(title='  Write thesis  ')
    assert task.title == 'Write thesis'

  def test_accepts_valid_title(self):
    task = create_task(title='Write thesis chapter')
    assert task.title == 'Write thesis chapter'

class TestEstimatedMinutesValidator:
  @pytest.mark.parametrize('input_val, expected', [
      (15, 15),
      (16, 30),
      (1, 15),
      (29, 30)
  ])

  def test_rounds_up_to_nearest_15(self, input_val, expected):
    task = create_task(estimated_minutes=input_val)
    assert task.estimated_minutes == expected

  def test_rejects_zero(self):
    with pytest.raises(ValueError, match='must be a positive integer'):
      create_task(estimated_minutes=0)

  def test_rejects_negative(self):
    with pytest.raises(ValueError, match='must be a positive integer'):
      create_task(estimated_minutes=-15)

  def test_accepts_none(self):
    task = create_task(estimated_minutes=None)
    assert task.estimated_minutes is None

  def test_none_by_default(self):
    task = create_task()
    assert task.estimated_minutes is None

class TestCompletedAtConsistency:
  def test_auto_sets_completed_at_on_completed_status(self):
    task = create_task(status=TaskStatus.COMPLETED)
    assert task.completed_at is not None

  def test_clears_completed_at_on_non_completed_status(self):
    task = create_task(status=TaskStatus.COMPLETED)
    assert task.completed_at is not None

    task = task.update(status=TaskStatus.PENDING)
    assert task.completed_at is None

# ------------------------------------------------------------------- #
# Public Interface                                                    #
# ------------------------------------------------------------------- #
class TestTaskCreate:
  def test_creates_task_with_given_fields(self):
    task = create_task(
      title=' Write thesis',
      description='Finish writing the thesis by the end of the month.',
      deadline=datetime(2024, 6, 30, tzinfo=UTC),
      planned_at=datetime(2024, 6, 29, tzinfo=UTC),
      estimated_minutes=115
    )
    assert task.title == 'Write thesis'
    assert task.description == 'Finish writing the thesis by the end of the month.'
    assert task.deadline == datetime(2024, 6, 30, tzinfo=UTC)
    assert task.planned_at == datetime(2024, 6, 29, tzinfo=UTC)
    assert task.estimated_minutes == 120
    assert task.status == TaskStatus.PENDING
    assert task.created_at is not None
    assert task.updated_at is not None
    assert task.id is not None

  def test_rejects_system_fields(self):
    with pytest.raises(ValueError, match='Cannot set system-managed fields: created_at, id'):
      create_task(
        title='Task',
        id=uuid4(),
        created_at=datetime(2000, 1, 1, tzinfo=timezone.utc)
      )

class TestTaskUpdate:
  def test_updates_given_fields(self):
    task = create_task(
      title='Task',
      description='Desc',
      estimated_minutes=20
    )
    time.sleep(0.01)
    updated = task.update(title=' New Task', estimated_minutes=35)

    assert updated.title == 'New Task'
    assert updated.description == 'Desc'
    assert updated.estimated_minutes == 45
    assert updated.updated_at > task.updated_at

  def test_ignores_immutable_fields(self):
    task = create_task(title='Task')
    updated = task.update(id=uuid4(), created_at=datetime(2000, 1, 1, tzinfo=timezone.utc))

    assert updated.id == task.id
    assert updated.created_at == task.created_at

  def test_rejects_unknown_fields(self):
    task = create_task(title='Task')
    with pytest.raises(ValueError, match='Unknown fields: bar, foo'):
      task.update(foo=123, bar='abc')

# pylint: disable=too-few-public-methods
class TestTaskDelete:
  def test_delete_method(self):
    task = create_task(title='Task')
    deleted = task.delete()
    assert deleted.status == TaskStatus.DELETED
    assert deleted is not task
# pylint: enable=too-few-public-methods

class TestTaskFind:
  def test_find_calls_repository_get(self, repository):
    task = create_task()
    repository.get.return_value = task.to_dict()
    Task.find(str(task.id))
    repository.get.assert_called_once_with(str(task.id))

  def test_find_returns_task_instance(self, repository):
    task = create_task()
    repository.get.return_value = task.to_dict()
    found = Task.find(str(task.id))
    assert isinstance(found, Task)
    assert found.id == task.id
    assert found.title == task.title

  def test_find_raises_if_task_not_found(self, repository):
    repository.get.side_effect = KeyError('not found')
    with pytest.raises(KeyError, match='not found'):
      Task.find('nonexistent-id')

  def test_find_raises_if_no_repository_set(self):
    Task.set_repository(None)
    with pytest.raises(ValueError, match='No repository set for Task model'):
      Task.find('some-id')

class TestTaskSearch:
  def test_search_calls_repository_list(self, repository):
    task1 = create_task(title='Task 1')
    task2 = create_task(title='Task 2')
    repository.list.return_value = [task1.to_dict(), task2.to_dict()]
    results = Task.search()
    repository.list.assert_called_once_with(None)
    assert len(results) == 2
    assert all(isinstance(t, Task) for t in results)
    assert {t.id for t in results} == {task1.id, task2.id}

  def test_search_with_query(self, repository):
    create_task(title='Task 1', status='pending')
    task2 = create_task(title='Task 2', status='completed')
    repository.list.return_value = [task2.to_dict()]

    results = Task.search(query={'status': 'completed'})
    assert len(results) == 1
    assert results[0].id == task2.id

  def test_search_returns_empty_list_if_no_matches(self, repository):
    repository.list.return_value = []
    results = Task.search(query={'status': 'nonexistent'})
    assert len(results) == 0

  def test_search_raises_if_no_repository_set(self):
    Task.set_repository(None)
    with pytest.raises(ValueError, match='No repository set for Task model'):
      Task.search()

# ------------------------------------------------------------------- #
# Serialization                                                       #
# ------------------------------------------------------------------- #
class TestTaskSerialization:
  def test_serializes_to_dict(self):
    task = create_task(title='Task', description='Desc', estimated_minutes=20)
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

# ------------------------------------------------------------------- #
# Repository Integration                                              #
# ------------------------------------------------------------------- #
class TestTaskRepositoryIntegration:
  def test_create_calls_repository_save(self, repository):
    create_task(title='Test Task')

    repository.save.assert_called_once()
    saved_data = repository.save.call_args[0][0]
    assert saved_data['title'] == 'Test Task'

  def test_update_calls_repository_save(self, repository):
    task = create_task(title='Original')
    repository.reset_mock()

    task.update(title='Updated')

    repository.save.assert_called_once()
    saved_data = repository.save.call_args[0][0]
    assert saved_data['title'] == 'Updated'

  def test_delete_calls_repository_save(self, repository):
    task = create_task()
    repository.reset_mock()  # Clear create call

    task.delete()

    repository.save.assert_called_once()
    saved_data = repository.save.call_args[0][0]
    assert saved_data['status'] == 'deleted'
