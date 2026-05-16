
import os
from pathlib import Path
from datetime import datetime, UTC, timedelta
import json
import pytest
from assistant_agent.models import Task
from assistant_agent.repository.json_repository import JsonRepository, JsonRepositoryError

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
# JsonRepository                                                     #
# ------------------------------------------------------------------ #
class TestJsonRepository:
  def test_save(self, tmp_path):
    repo = JsonRepository(root_path=tmp_path, file_name='test.json')
    task = create_task()
    task_dict = task.to_dict()
    repo.save(task_dict)

    with open(tmp_path / 'test.json', 'r', encoding='utf-8') as f:
      data = json.load(f)
    assert str(task.id) in data
    assert data[str(task.id)]['title'] == 'Test Task'

  def test_get(self, tmp_path):
    repo = JsonRepository(root_path=tmp_path, file_name='test.json')
    task = create_task()
    repo.save(task.to_dict())

    retrieved = repo.get(str(task.id))
    assert retrieved['id'] == str(task.id)
    assert retrieved['title'] == 'Test Task'

    with pytest.raises(KeyError, match='not found'):
      repo.get('nonexistent-id')

  def test_list(self, tmp_path):
    repo = JsonRepository(root_path=tmp_path, file_name='test.json')
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

  def test_file_creation(self):
    JsonRepository(file_name='test.json')
    file_path = Path.cwd() / 'data' / 'test.json'
    assert file_path.exists()

    os.remove(file_path)

  def test_data_persistence(self, tmp_path):
    repo1 = JsonRepository(root_path=tmp_path, file_name='test.json')
    task = create_task(title='Task 1')
    repo1.save(task.to_dict())

    repo2 = JsonRepository(root_path=tmp_path, file_name='test.json')
    retrieved = repo2.get(str(task.id))
    assert retrieved['id'] == str(task.id)

  def test_record_update(self, tmp_path):
    repo = JsonRepository(root_path=tmp_path, file_name='test.json')
    task = create_task(title='Original Title')
    repo.save(task.to_dict())

    task.title = 'Updated Title'
    repo.save(task.to_dict())

    retrieved = repo.get(str(task.id))
    assert len(repo.list()) == 1
    assert retrieved['id'] == str(task.id)
    assert retrieved['title'] == 'Updated Title'

  def test_file_integrity_on_save(self, tmp_path):
    repo = JsonRepository(root_path=tmp_path, file_name='test.json')
    task = create_task(title='Task 1')
    repo.save(task.to_dict())

    pytest.raises(JsonRepositoryError, lambda: repo.save('invalid data'))

    task2 = create_task(title='Task 2')
    repo.save(task2.to_dict())

    with open(tmp_path / 'test.json', 'r', encoding='utf-8') as f:
      data = json.load(f)
    assert str(task.id) in data
    assert str(task2.id) in data
    assert len(data) == 2
