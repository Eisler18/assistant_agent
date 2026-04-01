
from typing import List, Dict, Any
import json
import os
from assistant_agent.models import Task
from .base import BaseRepository

class JsonRepository(BaseRepository):
  def __init__(self, file_path: str = '../data/dump.json'):
    self.file_path = file_path
    self.encoding = 'utf-8'
    if not os.path.exists(file_path):
      with open(file_path, 'w', encoding=self.encoding) as f:
        json.dump({}, f)

  def save(self, task: Task) -> None:
    data = self.__read_file()
    data[str(task.id)] = task.to_dict()
    with open(self.file_path, 'w', encoding=self.encoding) as f:
      json.dump(data, f)

  def get(self, task_id: str) -> Task:
    data = self.__read_file()
    if task_id not in data:
      raise KeyError(f'Task with id {task_id} not found')
    return Task.from_dict(data[task_id])

  def list(self, query: Dict[str, Any] = None) -> List[Task]:
    data = self.__read_file()
    tasks = [Task.from_dict(item) for item in data.values()]

    if query is None:
      return tasks

    for key, value in query.items():
      tasks = [t for t in tasks if getattr(t, key) == value]
      if not tasks:
        break
    return tasks

  def __read_file(self) -> Dict[str, Any]:
    with open(self.file_path, 'r', encoding=self.encoding) as f:
      return json.load(f)
