
import os
from typing import List, Dict, Any
import json
from pathlib import Path
from .base import BaseRepository

class JsonRepository(BaseRepository):
  def __init__(self, root_path: str | Path | None = None, file_name: str = 'dump.json'):
    if root_path is None:
      root_path = Path.cwd() / 'data'

    self.root_path = Path(root_path)
    self.root_path.mkdir(parents=True, exist_ok=True)

    self.file_path = self.root_path / file_name
    self.encoding = 'utf-8'

    if not self.file_path.exists():
      with open(self.file_path, 'w', encoding=self.encoding) as f:
        json.dump({}, f)

  def save(self, task: Dict[str, Any]) -> None:
    data = self.__read_file()
    data[task['id']] = task
    tmp_path = self.file_path.with_suffix('.tmp')
    with open(tmp_path, 'w', encoding=self.encoding) as f:
      json.dump(data, f, indent=2)
    os.replace(tmp_path, self.file_path)

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
