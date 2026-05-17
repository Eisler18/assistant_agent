
from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
from .nodes import (
  intent_classifier_node,
  task_create_node,
  task_interrupt_node,
  task_delete_node,
  task_read_node,
  task_update_node
)
from .state import AgentState
from . import tools

# --- Helpers --- #
def _has_tool_calls(message: BaseMessage | None) -> bool:
  if message is None:
    return False
  tool_calls = getattr(message, 'tool_calls', None)
  return bool(tool_calls)


# --- Conditional routing functions --- #
def route_by_intent(state: AgentState) -> str:
  intent = state.get('intent', 'unknown')
  if intent in ('task_create', 'task_read', 'task_update', 'task_delete'):
    return intent
  return END

def should_continue(state: AgentState) -> str:
  messages = state.get('messages', [])
  last_message = messages[-1] if messages else None

  if not _has_tool_calls(last_message):
    return END
  tool_name = last_message.tool_calls[0]['name']

  intent = state.get('intent', 'unknown')
  if intent == 'task_read':
    return 'task_read_tools'

  if intent == 'task_create':
    if 'create_task' in tool_name and state.get('confirmation') is not True:
      return 'task_interrupt'

    return 'task_create_tools'

  return END

def should_save_task(state: AgentState) -> str:
  intent = state.get('intent', 'unknown')

  if intent == 'task_create':
    if state.get('confirmation') is True:
      return 'task_create_tools'
    if state.get('cancelled') is True:
      return END

    return 'task_create'

  return END


# --- Tool nodes --- #
_task_read_tools = ToolNode(tools.TASK_READ_TOOLS)
_task_create_tools = ToolNode(tools.TASK_CREATE_TOOLS)

# --- Graph construction --- #
_builder = StateGraph(AgentState)
_builder.add_node('intent_classifier', intent_classifier_node)
_builder.add_node('task_read', task_read_node)
_builder.add_node('task_read_tools', _task_read_tools)
_builder.add_node('task_create', task_create_node)
_builder.add_node('task_interrupt', task_interrupt_node)
_builder.add_node('task_create_tools', _task_create_tools)
_builder.add_node('task_update', task_update_node)
_builder.add_node('task_delete', task_delete_node)

_builder.add_edge(START, 'intent_classifier')
_builder.add_conditional_edges(
  'intent_classifier',
  route_by_intent,
  {
    'task_create': 'task_create',
    'task_read': 'task_read',
    'task_update': 'task_update',
    'task_delete': 'task_delete',
    END: END
  }
)

_builder.add_conditional_edges(
  'task_read',
  should_continue,
  {
    'task_read_tools': 'task_read_tools',
    END: END
  }
)
_builder.add_edge('task_read_tools', 'task_read')

_builder.add_conditional_edges(
  'task_create',
  should_continue,
  {
    'task_create_tools': 'task_create_tools',
    'task_interrupt': 'task_interrupt',
    END: END
  }
)
_builder.add_conditional_edges(
  'task_interrupt',
  should_save_task,
  {
    'task_create': 'task_create',
    'task_create_tools': 'task_create_tools',
    END: END
  }
)
_builder.add_edge('task_create_tools', 'task_create')
_builder.add_edge('task_interrupt', END)

_builder.add_edge('task_update', END)
_builder.add_edge('task_delete', END)

_checkpointer = InMemorySaver()
graph = _builder.compile(checkpointer=_checkpointer)
