
import math
from typing import Any, ClassVar, Optional
from uuid import uuid4
from datetime import date, datetime, UTC
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from pydantic.types import UUID4

_SYSTEM_FIELDS = { 'id', 'created_at', 'updated_at', 'completed_at' }

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

  repository: ClassVar[Optional[Any]] = None

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

  # Validators/Callbacks
  @model_validator(mode='after')
  def _completed_at_consistency(self) -> 'Task':
    if self.status == TaskStatus.COMPLETED and self.completed_at is None:
      object.__setattr__(self, 'completed_at', datetime.now(UTC))
    elif self.status != TaskStatus.COMPLETED and self.completed_at is not None:
      object.__setattr__(self, 'completed_at', None)
    return self

  @model_validator(mode='after')
  def _round_estimated_minutes(self) -> 'Task':
    if self.estimated_minutes is None:
      return self

    if self.estimated_minutes <= 0:
      raise ValueError('estimated_minutes must be a positive integer')

    rounded = math.ceil(self.estimated_minutes / 15) * 15
    object.__setattr__(self, 'estimated_minutes', rounded)
    return self

  @model_validator(mode='after')
  def _strip_title(self) -> 'Task':
    if not self.title.strip():
      raise ValueError('title must not be empty')
    object.__setattr__(self, 'title', self.title.strip())
    return self

  @classmethod
  def set_repository(cls, repository: Any) -> None:
    cls.repository = repository

  # Public Interface
  @classmethod
  def create(cls, **kwargs) -> 'Task':
    invalid_fields = kwargs.keys() & _SYSTEM_FIELDS
    if invalid_fields:
      raise ValueError(f"Cannot set system-managed fields: {', '.join(sorted(invalid_fields))}")

    task = cls(**kwargs)
    if cls.repository is not None:
      cls.repository.save(task.to_dict())
    return task

  def update(self, **kwargs) -> 'Task':
    attributes = Task.model_fields.keys()

    unknown_or_immutable = [k for k in kwargs if k not in attributes or k in _SYSTEM_FIELDS]
    if any(unknown_or_immutable):
      raise ValueError(
        f"Unknown or non-updatable fields: {', '.join(sorted(unknown_or_immutable))}"
      )

    task =  self.model_validate(
      self.model_copy(update={ **kwargs, 'updated_at': datetime.now(UTC) })
    )
    if self.__class__.repository is not None:
      self.__class__.repository.save(task.to_dict())
    return task

  def delete(self) -> 'Task':
    return self.update(status=TaskStatus.DELETED)

  # Serialization
  def to_dict(self) -> dict[str, Any]:
    return self.model_dump(mode='json')

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> "Task":
    return cls.model_validate(data)
