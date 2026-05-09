
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

IntentType = Literal['task_crud', 'briefing', 'unknown']

class AgentState(TypedDict):
  messages: Annotated[list, add_messages]
  intent: IntentType
