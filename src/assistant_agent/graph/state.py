
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

IntentType = Literal[
  'task_create',
  'task_read',
  'task_update',
  'unknown'
]

class AgentState(TypedDict):
  messages: Annotated[list, add_messages]
  intent: IntentType
  confirmation: bool | None
  cancelled: bool | None
  briefing_shown: bool
