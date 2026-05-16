
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

from ..models import Task

IntentType = Literal[
  'task_create',
  'task_read',
  'task_update',
  'task_delete',
  'unknown'
]

class AgentState(TypedDict):
  messages: Annotated[list, add_messages]
  intent: IntentType
  tasks: list[Task] | None
  task_id: str | None
  confirmation: bool | None
  cancelled: bool | None
