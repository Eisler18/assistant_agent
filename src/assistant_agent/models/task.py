
import math
from pydantic import BaseModel, Field, field_validator, model_validator
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

  # Validators
  @field_validator('title')
  @classmethod
  def not_empty_title(cls, v):
    if not v.strip():
      raise ValueError("title must not be empty")
    return v.strip()
  
  @field_validator('estimated_minutes')
  @classmethod
  def round_estimated_minutes(cls, v):
    if v is None:
      return None
    if v <= 0:
      raise ValueError("estimated_minutes must be a positive integer")
    return math.ceil(v / 15) * 15

  # Callbacks
  @model_validator(mode='after')
  def completed_at_consistency(self) -> "Task":
    if self.status == TaskStatus.COMPLETED and self.completed_at is None:
      object.__setattr__(self, "completed_at", datetime.now(UTC))
    elif self.status != TaskStatus.COMPLETED and self.completed_at is not None:
      object.__setattr__(self, "completed_at", None)
    return self

