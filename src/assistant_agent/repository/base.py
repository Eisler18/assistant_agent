from abc import ABC, abstractmethod
from typing import Any, Dict, List
from assistant_agent.models import Task

class BaseRepository(ABC):
  @abstractmethod
  def __init__(self):
    pass

  @abstractmethod
  def save(self, task: Task) -> None:
    pass

  @abstractmethod
  def get(self, task_id: str) -> Task:
    pass

  @abstractmethod
  def list(self, query: Dict[str, Any]) -> List[Task]:
    pass
