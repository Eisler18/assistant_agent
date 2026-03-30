
from assistant_agent.models.task import TaskStatus

# ------------------------------------------------------------------ #
# TaskStatus                                                         #
# ------------------------------------------------------------------ #

class TestTaskStatus:
  def test_values_are_strings(self):
    '''TaskStatus inherits from str — values must be plain strings.'''
    assert TaskStatus.PENDING == 'pending'
    assert TaskStatus.COMPLETED == 'completed'
    assert TaskStatus.DELETED == 'deleted'

  def test_is_str_subclass(self):
    assert isinstance(TaskStatus.PENDING, str)
