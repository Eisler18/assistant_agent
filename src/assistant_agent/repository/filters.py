from datetime import datetime
from typing import TypedDict

class TaskFilter(TypedDict, total=False):
  status: str
  planned_at_gte: datetime
  planned_at_lte: datetime
  deadline_lte: datetime
  has_deadline: bool
  has_planned_at: bool
