
from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from .nodes import briefing_node, intent_classifier_node, task_crud_node
from .state import AgentState
from . import tools

# --- Helpers --- #
def _has_tool_calls(message: BaseMessage | None) -> bool:
  if message is None:
    return False
  tool_calls = getattr(message, 'tool_calls', None)
  return bool(tool_calls)

def _build_query_tools() -> list:
  return [
    tools.parse_date,
    tools.parse_date_range,
    tools.build_overdue_filter,
    tools.build_today_filter,
    tools.build_unscheduled_filter,
    tools.get_task,
    tools.list_tasks
  ]

def _build_task_tools() -> list:
  return [
    tools.create_task,
    tools.update_task,
    tools.delete_task,
    *_build_query_tools()
  ]

def _build_briefing_tools() -> list:
  return [
    tools.get_daily_briefing_data,
    *_build_query_tools()
  ]

# --- Conditional routing functions --- #
def route_by_intent(state: AgentState) -> str:
  intent = state.get('intent', 'unknown')
  if intent in ('task_crud', 'briefing'):
    return intent
  return END

def should_continue(state: AgentState) -> str:
  messages = state.get('messages', [])
  last_message = messages[-1] if messages else None

  if not _has_tool_calls(last_message):
    return END

  intent = state.get('intent', 'unknown')
  if intent == 'task_crud':
    return 'task_tools'
  if intent == 'briefing':
    return 'briefing_tools'

  return END


# --- Tool nodes --- #
_task_tools = ToolNode(_build_task_tools())
_briefing_tools = ToolNode(_build_briefing_tools())

# --- Graph construction --- #
_builder = StateGraph(AgentState)
_builder.add_node('intent_classifier', intent_classifier_node)
_builder.add_node('task_crud', task_crud_node)
_builder.add_node('briefing', briefing_node)
_builder.add_node('task_tools', _task_tools)
_builder.add_node('briefing_tools', _briefing_tools)

_builder.add_edge(START, 'intent_classifier')
_builder.add_conditional_edges(
  'intent_classifier',
  route_by_intent,
  {
    'task_crud': 'task_crud',
    'briefing': 'briefing',
    END: END
  }
)

_builder.add_conditional_edges(
  'task_crud',
  should_continue,
  {
    'task_tools': 'task_tools',
    END: END
  }
)
_builder.add_edge('task_tools', 'task_crud')

_builder.add_conditional_edges(
  'briefing',
  should_continue,
  {
    'briefing_tools': 'briefing_tools',
    END: END
  }
)
_builder.add_edge('briefing_tools', 'briefing')

graph = _builder.compile()
