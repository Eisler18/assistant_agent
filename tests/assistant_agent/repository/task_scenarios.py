
from datetime import UTC, datetime, timedelta

import pytest
from assistant_agent.models import Task
from assistant_agent.repository.base import BaseRepository


def create_task(**kwargs) -> Task:
  '''Helper to create a task with default values for testing'''
  defaults = {
    'title': 'Test Task',
    'description': 'A task for testing'
  }
  return Task.create(**{**defaults, **kwargs})


def assert_get_and_not_found(repo: BaseRepository, task) -> None:
  '''
  Shared get()/KeyError contract, exercised against any BaseRepository
  implementation. `task` must already be saved in `repo`.
  '''
  retrieved = repo.get(str(task.id))
  assert retrieved['id'] == str(task.id)
  assert retrieved['title'] == task.title

  with pytest.raises(KeyError, match='not found'):
    repo.get('nonexistent-id')


def assert_list_filters(repo: BaseRepository) -> None:
  '''
  Shared TaskFilter contract, exercised against any BaseRepository
  implementation (JsonRepository, PostgresRepository, ...).
  '''
  base = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
  planned_at_later = base + timedelta(days=1)
  deadline_early = base + timedelta(days=2)
  deadline_late = base + timedelta(days=4)

  task_a = create_task(
    title='Task A',
    status='pending',
    planned_at=base,
    deadline=deadline_late
  )
  task_b = create_task(
    title='Task B',
    status='completed',
    planned_at=planned_at_later,
    deadline=deadline_early
  )
  task_c = create_task(
    title='Task C',
    status='pending',
    planned_at=None,
    deadline=deadline_early
  )
  task_d = create_task(
    title='Task D',
    status='pending',
    planned_at=planned_at_later,
    deadline=None
  )
  task_deleted = create_task(
    title='Task Deleted',
    status='deleted',
    planned_at=base,
    deadline=deadline_early
  )

  for task in (task_a, task_b, task_c, task_d, task_deleted):
    repo.save(task.to_dict())

  def task_ids(tasks):
    return {task['id'] for task in tasks}

  assert task_ids(repo.list()) == {
    str(task_a.id),
    str(task_b.id),
    str(task_c.id),
    str(task_d.id)
  }
  assert task_ids(repo.list(query={'status': 'completed'})) == {str(task_b.id)}
  assert task_ids(repo.list(query={'status': 'deleted'})) == set()

  assert task_ids(repo.list(query={'planned_at_gte': base})) == {
    str(task_a.id),
    str(task_b.id),
    str(task_d.id)
  }
  assert task_ids(repo.list(query={'planned_at_gte': planned_at_later})) == {
    str(task_b.id),
    str(task_d.id)
  }
  assert task_ids(repo.list(query={'planned_at_lte': base})) == {str(task_a.id)}

  assert task_ids(repo.list(query={'deadline_lte': deadline_early})) == {
    str(task_b.id),
    str(task_c.id)
  }

  assert task_ids(repo.list(query={'has_deadline': True})) == {
    str(task_a.id),
    str(task_b.id),
    str(task_c.id)
  }
  assert task_ids(repo.list(query={'has_deadline': False})) == {str(task_d.id)}

  assert task_ids(repo.list(query={'has_planned_at': True})) == {
    str(task_a.id),
    str(task_b.id),
    str(task_d.id)
  }
  assert task_ids(repo.list(query={'has_planned_at': False})) == {str(task_c.id)}

  assert task_ids(
    repo.list(query={'status': 'pending', 'planned_at_gte': planned_at_later})
  ) == {str(task_d.id)}
  assert task_ids(
    repo.list(query={'planned_at_gte': planned_at_later, 'planned_at_lte': base})
  ) == set()
