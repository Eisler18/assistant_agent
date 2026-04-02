
import pytest
from assistant_agent.repository.base import BaseRepository

# ------------------------------------------------------------------ #
# Helpers                                                            #
# ------------------------------------------------------------------ #
class IncompleteRepo(BaseRepository):
  def save(self, task):
    pass

class CompleteRepo(BaseRepository):
  def save(self, task):
    pass
  def get(self, task_id):
    pass
  def list(self, query=None):
    pass

class TestBaseRepository:
  def test_abstract_methods(self):
    with pytest.raises(TypeError):
      BaseRepository()  # pylint: disable=abstract-class-instantiated

  def test_incomplete_implementation(self):
    with pytest.raises(TypeError):
      IncompleteRepo()  # pylint: disable=abstract-class-instantiated

  def test_complete_implementation(self):
    CompleteRepo()
