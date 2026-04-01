
from typing import List, Dict, Any
import json
import os
from .base import BaseRepository

class JsonRepository(BaseRepository):
  def __init__(self, file_path: str = '../data/dump.json'):
    self.file_path = file_path
    self.encoding = 'utf-8'
    if not os.path.exists(file_path):
      with open(file_path, 'w', encoding=self.encoding) as f:
        json.dump({}, f)

  def save(self, task: Dict[str, Any]) -> None:
    data = self.__read_file()
    data[task['id']] = task
    with open(self.file_path, 'w', encoding=self.encoding) as f:
      json.dump(data, f)

  def get(self, task_id: str) -> Dict[str, Any]:
    data = self.__read_file()
    if task_id not in data:
      raise KeyError(f'Task with id {task_id} not found')
    return data[task_id]

  def list(self, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    data = self.__read_file()
    tasks = list(data.values())

    if query is None:
      return tasks

    for key, value in query.items():
      tasks = [t for t in tasks if t.get(key, None) == value]
      if not tasks:
        break
    return tasks

  def __read_file(self) -> Dict[str, Any]:
    with open(self.file_path, 'r', encoding=self.encoding) as f:
      return json.load(f)
