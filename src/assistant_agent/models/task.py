
import math
from pydantic import BaseModel, Field, field_validator
from pydantic.types import UUID4
from uuid import uuid4
from datetime import date, datetime, UTC
from enum import Enum

class TaskStatus(str, Enum):
  '''
  Task lifecycle states
  '''

  PENDING = 'pending'
  COMPLETED = 'completed'
  DELETED = 'deleted'

class Task(BaseModel):
  '''
  Task entity for the time management assistant
  '''

  id: UUID4 = Field(default_factory=uuid4)
  title: str
  description: str | None = None
  deadline: date | None = None
  planned_date: date | None = None
  estimated_minutes: int | None = None
  status: TaskStatus = TaskStatus.PENDING
  created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
  updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
  completed_at: datetime | None = None
