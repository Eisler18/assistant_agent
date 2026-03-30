
from datetime import datetime, UTC

import pytest

from assistant_agent.models.task import Task, TaskStatus

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

# ------------------------------------------------------------------ #
# Task Validators                                                    #
# ------------------------------------------------------------------ #
class TestTitleValidator:
  def test_rejects_empty_string(self):
    with pytest.raises(ValueError, match="title must not be empty"):
      Task(title="")

  def test_rejects_whitespace_only(self):
    with pytest.raises(ValueError, match="title must not be empty"):
      Task(title="   ")

  def test_strips_surrounding_whitespace(self):
    task = Task(title="  Write thesis  ")
    assert task.title == "Write thesis"

  def test_accepts_valid_title(self):
    task = Task(title="Write thesis chapter")
    assert task.title == "Write thesis chapter"

class TestEstimatedMinutesValidator:
  @pytest.mark.parametrize("input_val, expected", [
      (15, 15),
      (16, 30),
      (1, 15),
      (29, 30)
  ])

  def test_rounds_up_to_nearest_15(self, input_val, expected):
    task = Task(title="Task", estimated_minutes=input_val)
    assert task.estimated_minutes == expected

  def test_rejects_zero(self):
    with pytest.raises(ValueError, match="must be a positive integer"):
      Task(title="Task", estimated_minutes=0)

  def test_rejects_negative(self):
    with pytest.raises(ValueError, match="must be a positive integer"):
      Task(title="Task", estimated_minutes=-15)

  def test_accepts_none(self):
    task = Task(title="Task", estimated_minutes=None)
    assert task.estimated_minutes is None

  def test_none_by_default(self):
    task = Task(title="Task")
    assert task.estimated_minutes is None

# ------------------------------------------------------------------ #
# Task Callbacks                                                     #
# ------------------------------------------------------------------ #
class TestCompletedAtConsistency:
  def test_auto_sets_completed_at_on_completed_status(self):
    task = Task(title="Task", status=TaskStatus.COMPLETED)
    assert task.completed_at is not None

  def test_clears_completed_at_on_non_completed_status(self):
    task = Task(title="Task", status=TaskStatus.PENDING, completed_at=datetime.now(UTC))
    assert task.completed_at is None

# ------------------------------------------------------------------- #
# Public API                                                          #
# ------------------------------------------------------------------- #

