
import os
from pathlib import Path
import json
import pytest
from task_scenarios import assert_get_and_not_found, assert_list_filters, create_task
from assistant_agent.repository.json_repository import JsonRepository, JsonRepositoryError

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

    assert_get_and_not_found(repo, task)

  def test_list(self, tmp_path):
    repo = JsonRepository(root_path=tmp_path, file_name='test.json')
    assert_list_filters(repo)

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
