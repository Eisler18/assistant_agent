from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseRepository(ABC):
  @abstractmethod
  def save(self, task: Dict[str, Any]) -> None:
    pass

  @abstractmethod
  def get(self, task_id: str) -> Dict[str, Any]:
    pass

  @abstractmethod
  def list(self, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    pass
