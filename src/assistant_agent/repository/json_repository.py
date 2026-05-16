
import os
from typing import List, Dict, Any
import json
from pathlib import Path

from .base import BaseRepository
from ..utils.date_parser import str_to_datetime, ensure_utc
from .filters import TaskFilter

class JsonRepositoryError(Exception):
  pass

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
    try:
      data = self.__read_file()
      data[task['id']] = task
      tmp_path = self.file_path.with_suffix('.tmp')
      with open(tmp_path, 'w', encoding=self.encoding) as f:
        json.dump(data, f, indent=2)
      os.replace(tmp_path, self.file_path)
    except (TypeError, json.JSONDecodeError) as e:
      raise JsonRepositoryError("Failed to save task") from e

  def get(self, task_id: str) -> Dict[str, Any]:
    data = self.__read_file()
    if task_id not in data:
      raise KeyError(f'Task with id {task_id} not found')
    return data[task_id]

  def list(self, query: TaskFilter | None = None) -> List[Dict[str, Any]]:
    data = self.__read_file()
    tasks = list(data.values())

    if query is None:
      query = {}

    return [task for task in tasks if self._matches(task, query)]

  def _matches(self, task_dict: Dict[str, Any], query: TaskFilter) -> bool:
    # Exclude deleted tasks by default
    if task_dict.get('status') == 'deleted':
      return False

    match = True
    # Status filter
    status = query.get('status')
    if status is not None:
      match = match and task_dict.get('status') == status

    # Planned at filter
    planned_at = str_to_datetime(task_dict.get('planned_at'))

    planned_at_gte = ensure_utc(query.get('planned_at_gte'))
    if planned_at_gte is not None:
      match = match and planned_at is not None and planned_at >= planned_at_gte

    planned_at_lte = ensure_utc(query.get('planned_at_lte'))
    if planned_at_lte is not None:
      match = match and planned_at is not None and planned_at <= planned_at_lte

    has_planned_at = query.get('has_planned_at')
    if has_planned_at is not None:
      match = match and (planned_at is not None) == has_planned_at

    # Deadline filter
    deadline = str_to_datetime(task_dict.get('deadline'))
    deadline_lte = ensure_utc(query.get('deadline_lte'))
    if deadline_lte is not None:
      match = match and deadline is not None and deadline <= deadline_lte

    has_deadline = query.get('has_deadline')
    if has_deadline is not None:
      match = match and (deadline is not None) == has_deadline

    return match

  def __read_file(self) -> Dict[str, Any]:
    with open(self.file_path, 'r', encoding=self.encoding) as f:
      return json.load(f)
