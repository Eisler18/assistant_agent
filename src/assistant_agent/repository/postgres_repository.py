
from typing import Any, Dict, List

from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .base import BaseRepository
from .engine import build_engine
from .filters import TaskFilter
from .schema import tasks
from ..utils.date_parser import ensure_utc, str_to_datetime

_DATETIME_FIELDS = ('deadline', 'planned_at', 'created_at', 'updated_at', 'completed_at')


class PostgresRepository(BaseRepository):
  def __init__(self, database_url: str | None = None, engine: Engine | None = None):
    if engine is None:
      if not database_url:
        raise ValueError('Either database_url or engine must be provided')
      engine = build_engine(database_url)
    self.engine = engine

  def save(self, task: Dict[str, Any]) -> None:
    row = self._to_row(task)
    stmt = pg_insert(tasks).values(**row)
    stmt = stmt.on_conflict_do_update(index_elements=['id'], set_=row)
    with self.engine.begin() as conn:
      conn.execute(stmt)

  def get(self, task_id: str) -> Dict[str, Any]:
    stmt = select(tasks).where(tasks.c.id == task_id)
    with self.engine.connect() as conn:
      row = conn.execute(stmt).mappings().first()
    if row is None:
      raise KeyError(f'Task with id {task_id} not found')
    return self._from_row(row)

  def list(self, query: TaskFilter | None = None) -> List[Dict[str, Any]]:
    stmt = select(tasks).where(*self._conditions(query or {}))
    with self.engine.connect() as conn:
      rows = conn.execute(stmt).mappings().all()
    return [self._from_row(row) for row in rows]

  def _conditions(self, query: TaskFilter) -> list:
    # Exclude deleted tasks by default
    conditions = [tasks.c.status != 'deleted']

    status = query.get('status')
    if status is not None:
      conditions.append(tasks.c.status == status)

    planned_at_gte = ensure_utc(query.get('planned_at_gte'))
    if planned_at_gte is not None:
      conditions.append(tasks.c.planned_at >= planned_at_gte)

    planned_at_lte = ensure_utc(query.get('planned_at_lte'))
    if planned_at_lte is not None:
      conditions.append(tasks.c.planned_at <= planned_at_lte)

    has_planned_at = query.get('has_planned_at')
    if has_planned_at is not None:
      planned_at_condition = tasks.c.planned_at.is_not(None) if has_planned_at \
        else tasks.c.planned_at.is_(None)
      conditions.append(planned_at_condition)

    deadline_lte = ensure_utc(query.get('deadline_lte'))
    if deadline_lte is not None:
      conditions.append(tasks.c.deadline <= deadline_lte)

    has_deadline = query.get('has_deadline')
    if has_deadline is not None:
      deadline_condition = tasks.c.deadline.is_not(None) if has_deadline \
        else tasks.c.deadline.is_(None)
      conditions.append(deadline_condition)

    return conditions

  def _to_row(self, task: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(task)
    for field in _DATETIME_FIELDS:
      if field in row and isinstance(row[field], str):
        row[field] = str_to_datetime(row[field])
    return row

  def _from_row(self, row) -> Dict[str, Any]:
    data = dict(row)
    for field in _DATETIME_FIELDS:
      if data.get(field) is not None:
        data[field] = data[field].isoformat()
    return data
