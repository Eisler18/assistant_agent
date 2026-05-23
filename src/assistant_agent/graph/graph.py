
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
from .nodes import (
  after_initialiser_node,
  intent_classifier_node,
  session_initialiser_node,
  task_create_node,
  task_interrupt_node,
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
  if intent in ('task_create', 'task_read', 'task_update'):
    return intent
  return END

def should_continue(state: AgentState) -> str:
  messages = state.get('messages', [])
  last_message = messages[-1] if messages else None
  result = END

  if _has_tool_calls(last_message):
    tool_name = last_message.tool_calls[0]['name']
    intent = state.get('intent', 'unknown')
    if intent == 'task_read':
      result = 'task_read_tools'
    elif intent == 'task_create':
      if 'create_task' in tool_name and state.get('confirmation') is not True:
        result = 'task_interrupt'
      else:
        result = 'task_create_tools'
    elif intent == 'task_update':
      if (
        tool_name in {'update_task', 'delete_task'}
        and state.get('confirmation') is not True
      ):
        result = 'task_interrupt'
      else:
        result = 'task_update_tools'

  return result

def should_save_task(state: AgentState) -> str:
  intent = state.get('intent', 'unknown')
  result = END

  if intent == 'task_create':
    if state.get('confirmation') is True:
      result = 'task_create_tools'
    elif state.get('cancelled') is True:
      result = END
    else:
      result = 'task_create'

  elif intent == 'task_update':
    if state.get('confirmation') is True:
      result = 'task_update_tools'
    elif state.get('cancelled') is True:
      result = END
    else:
      result = 'task_update'

  return result

def route_after_initialiser(state: AgentState) -> str:
  if state.get('briefing_shown', False):
    return 'intent_classifier'

  messages = state.get('messages', [])
  last_message = messages[-1] if messages else None
  if _has_tool_calls(last_message):
    return 'briefing_tools'

  return 'after_initialiser'


# --- Tool nodes --- #
_task_read_tools = ToolNode(tools.TASK_READ_TOOLS)
_task_create_tools = ToolNode(tools.TASK_CREATE_TOOLS)
_task_update_tools = ToolNode(tools.TASK_UPDATE_TOOLS)
_briefing_tools = ToolNode(tools.BRIEFING_TOOLS)

# --- Graph construction --- #
_builder = StateGraph(AgentState)
_builder.add_node('session_initialiser', session_initialiser_node)
_builder.add_node('after_initialiser', after_initialiser_node)
_builder.add_node('briefing_tools', _briefing_tools)
_builder.add_node('intent_classifier', intent_classifier_node)
_builder.add_node('task_read', task_read_node)
_builder.add_node('task_read_tools', _task_read_tools)
_builder.add_node('task_create', task_create_node)
_builder.add_node('task_interrupt', task_interrupt_node)
_builder.add_node('task_create_tools', _task_create_tools)
_builder.add_node('task_update', task_update_node)
_builder.add_node('task_update_tools', _task_update_tools)

_builder.add_edge(START, 'session_initialiser')
_builder.add_conditional_edges(
  'session_initialiser',
  route_after_initialiser,
  {
    'briefing_tools': 'briefing_tools',
    'intent_classifier': 'intent_classifier',
    'after_initialiser': 'after_initialiser'
  }
)
_builder.add_edge('briefing_tools', 'session_initialiser')
_builder.add_edge('after_initialiser', END)

_builder.add_conditional_edges(
  'intent_classifier',
  route_by_intent,
  {
    'task_create': 'task_create',
    'task_read': 'task_read',
    'task_update': 'task_update',
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
  'task_update',
  should_continue,
  {
    'task_update_tools': 'task_update_tools',
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
    'task_update': 'task_update',
    'task_update_tools': 'task_update_tools',
    END: END
  }
)
_builder.add_edge('task_create_tools', 'task_create')
_builder.add_edge('task_update_tools', 'task_update')
_builder.add_edge('task_interrupt', END)

_checkpointer = InMemorySaver()
graph = _builder.compile(checkpointer=_checkpointer)
