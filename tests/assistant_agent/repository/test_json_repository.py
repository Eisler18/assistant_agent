
import json
import pytest
from assistant_agent.models import Task
from assistant_agent.repository.json_repository import JsonRepository

class TestJsonRepository:
  def test_save(self, tmp_path):
    repo = JsonRepository(file_path=tmp_path / 'test.json')
    task = Task.create(title='Test Task')
    repo.save(task)

    with open(tmp_path / 'test.json', 'r', encoding='utf-8') as f:
      data = json.load(f)
    assert str(task.id) in data
    assert data[str(task.id)]['title'] == 'Test Task'

  def test_get(self, tmp_path):
    repo = JsonRepository(file_path=tmp_path / 'test.json')
    task = Task.create(title='Test Task')
    repo.save(task)

    retrieved = repo.get(str(task.id))
    assert retrieved.id == task.id
    assert retrieved.title == 'Test Task'

    with pytest.raises(KeyError, match='not found'):
      repo.get('nonexistent-id')

  def test_list(self, tmp_path):
    repo = JsonRepository(file_path=tmp_path / 'test.json')
    task1 = Task.create(title='Task 1', status='pending')
    task2 = Task.create(title='Task 2', status='completed')
    repo.save(task1)
    repo.save(task2)

    all_tasks = repo.list()
    assert len(all_tasks) == 2

    pending_tasks = repo.list(query={'status': 'pending'})
    assert len(pending_tasks) == 1
    assert pending_tasks[0].id == task1.id

    empty_tasks = repo.list(query={'status': 'nonexistent'})
    assert len(empty_tasks) == 0
