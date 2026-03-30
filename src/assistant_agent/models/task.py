
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

  id: UUID4 = Field(default_factory=uuid4, frozen=True)
  title: str
  description: str | None = None
  deadline: date | None = None
  planned_date: date | None = None
  estimated_minutes: int | None = None
  status: TaskStatus = TaskStatus.PENDING
  created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), frozen=True)
  updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
  completed_at: datetime | None = None

  # Validators
  @field_validator('title')
  @classmethod
  def not_empty_title(cls, v):
    if not v.strip():
      raise ValueError('title must not be empty')
    return v
  
  @field_validator('estimated_minutes')
  @classmethod
  def positive_integer(cls, v):
    if v is None:
      return None
    if v <= 0:
      raise ValueError('estimated_minutes must be a positive integer')
    return v

  # Callbacks
  @model_validator(mode='after')
  def _completed_at_consistency(self) -> 'Task':
    if self.status == TaskStatus.COMPLETED and self.completed_at is None:
      object.__setattr__(self, 'completed_at', datetime.now(UTC))
    elif self.status != TaskStatus.COMPLETED and self.completed_at is not None:
      object.__setattr__(self, 'completed_at', None)
    return self
  
  @model_validator(mode='after')
  def _round_estimated_minutes(self) -> 'Task':
    if self.estimated_minutes is not None:
      rounded = math.ceil(self.estimated_minutes / 15) * 15
      object.__setattr__(self, 'estimated_minutes', rounded)
    return self
  
  @model_validator(mode='after')
  def _strip_title(self) -> 'Task':
    object.__setattr__(self, 'title', self.title.strip())
    return self
  
  # Public Interface
  @classmethod
  def create(cls, **kwargs) -> 'Task':
    return cls(**kwargs)
  
  def update(self, **kwargs) -> 'Task':
    attributes = Task.model_fields.keys()

    if any(k not in attributes for k in kwargs):
      raise ValueError(f"Unknown fields: {', '.join(k for k in kwargs if k not in attributes)}")
    
    for k in ['id', 'created_at']:
      kwargs.pop(k, None)

    return self.model_validate(self.model_copy(update={ **kwargs, 'updated_at': datetime.now(UTC) }))
  
  def delete(self) -> 'Task':
    return self.update(status=TaskStatus.DELETED)
