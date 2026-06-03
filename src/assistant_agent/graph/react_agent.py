from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage

from .state import AgentState
from .nodes import task_interrupt_node, _sanitize_tool_calls
from . import tools
from ..config import Config

config = Config()

ALL_TOOLS = [
  tools.create_task,
  tools.new_task,
  tools.get_task,
  tools.list_tasks,
  tools.update_task,
  tools.delete_task,
  tools.parse_date_range,
  tools.build_overdue_filter,
  tools.build_today_filter,
  tools.build_unscheduled_filter,
  tools.build_stale_filter,
  tools.format_task_preview,
  tools.get_daily_briefing_data,
  tools.generate_calendar_link
]

_WRITE_TOOLS = { 'create_task', 'update_task', 'delete_task' }

SYSTEM_PROMPT = '''You are a personal time management assistant.
You help users manage tasks: create, read, update, and delete them.
You also provide a daily briefing at the start of each session.

Rules:
- Always use tools for date parsing; never parse dates yourself.
- Always use a filter builder before calling list_tasks.
- Show task details using format_task_preview.
- After creating or updating a task with a planned_at, show a Google Calendar link.
'''

def react_agent_node(state: AgentState) -> dict:
  messages = [SystemMessage(content=SYSTEM_PROMPT), *state['messages']]
  llm_with_tools = config.llm.bind_tools(ALL_TOOLS)
  response = llm_with_tools.invoke(messages)
  sanitized = _sanitize_tool_calls(response)
  return {
    'messages': [sanitized],
    'confirmation': None,
    'cancelled': None
  }

def should_continue(state: AgentState) -> str:
  messages = state.get('messages', [])
  last = messages[-1] if messages else None
  if not last or not getattr(last, 'tool_calls', None):
    return END
  tool_name = last.tool_calls[0]['name']
  if tool_name in _WRITE_TOOLS and state.get('confirmation') is not True:
    return 'task_interrupt'
  return 'tools'

def should_save(state: AgentState) -> str:
  if state.get('confirmation') is True:
    return 'tools'
  if state.get('cancelled') is True:
    return END
  return 'react_agent'

_tool_node = ToolNode(ALL_TOOLS)

_builder = StateGraph(AgentState)
_builder.add_node('react_agent', react_agent_node)
_builder.add_node('tools', _tool_node)
_builder.add_node('task_interrupt', task_interrupt_node)

_builder.add_edge(START, 'react_agent')
_builder.add_conditional_edges('react_agent', should_continue, {
  'tools': 'tools',
  'task_interrupt': 'task_interrupt',
  END: END
})
_builder.add_edge('tools', 'react_agent')
_builder.add_conditional_edges('task_interrupt', should_save, {
  'tools': 'tools',
  'react_agent': 'react_agent',
  END: END
})

_checkpointer = InMemorySaver()
react_agent = _builder.compile(checkpointer=_checkpointer)
