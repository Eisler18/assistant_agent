
from typing import get_args

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.tools import ToolException
from langgraph.types import interrupt

from ..config import Config
from ..utils.date_parser import coerce_datetime
from . import tools
from .state import AgentState, IntentType

config = Config()

# --- Helper functions --- #
def _parse_intent(content: object) -> str:
  if isinstance(content, str):
    intent = content.strip()
    if intent in set(get_args(IntentType)):
      return intent
  return 'unknown'

def _sanitize_tool_calls(message: AIMessage) -> AIMessage:
  tool_calls = getattr(message, 'tool_calls', None)
  if not tool_calls:
    return message

  sanitized = []
  for call in tool_calls:
    name = call.get('name', '')
    if '<|' in name:
      name = name.split('<|', 1)[0]
    sanitized.append({
      **call,
      'name': name
    })

  return AIMessage(
    content=message.content,
    additional_kwargs=message.additional_kwargs,
    response_metadata=message.response_metadata,
    id=message.id,
    tool_calls=sanitized,
    invalid_tool_calls=message.invalid_tool_calls,
    usage_metadata=message.usage_metadata
  )

def _confirm_preview(question: str, details: str, cancel_message: str) -> dict:
  user_response = interrupt({
    'question': question,
    'details': details
  })

  confirmed = 'yes' in user_response.strip().lower()
  cancelled = 'no' in user_response.strip().lower()

  if not(confirmed or cancelled):
    return { 'messages': [HumanMessage(content=user_response)] }
  if cancelled:
    return { 'messages': [AIMessage(content=cancel_message)], 'cancelled': True }

  return { 'confirmation': confirmed }

def _handle_create_interrupt(target_call: dict) -> dict:
  preview_tasks = tools.new_task.run(target_call['args'])
  question = 'Do you confirm the current task details? ' \
    'Reply yes to confirm, add more details or no to cancel.'
  details = tools.format_task_preview.run(preview_tasks)
  cancel_message = 'Task creation cancelled.'
  return _confirm_preview(question, details, cancel_message)

def _find_task(task_id: str) -> dict:
  try:
    current = tools.get_task.run({ 'task_id': task_id })
    return current['tasks'][0]
  except Exception as e:
    raise ToolException(f'Failed to retrieve task details for task_id: {task_id}') from e

def _handle_update_interrupt(target_call: dict) -> dict:
  task_dict = _find_task(target_call['args'].get('task_id'))

  updated_fields = {}
  for key, value in target_call['args'].items():
    if key != 'task_id' and value is not None:
      if key in {'planned_at', 'deadline'}:
        updated_fields[key] = coerce_datetime(value)
      else:
        updated_fields[key] = value

  task_dict.update(updated_fields)
  question = 'Do you confirm the updated task details? ' \
    'Reply yes to confirm, add more details or no to cancel.'
  details = tools.format_task_preview.run({ 'tasks': [task_dict] })
  cancel_message = f'Update of task "{task_dict.get("title", "Untitled Task")}" cancelled.'
  return _confirm_preview(question, details, cancel_message)

def _handle_delete_interrupt(target_call: dict) -> dict:
  task_dict = _find_task(target_call['args'].get('task_id'))

  task_title = task_dict.get('title', 'Untitled Task')
  details = f'Task: {task_title}'
  question = f'Do you want to delete the task "{task_title}"? Reply yes to confirm or no to cancel.'
  cancel_message = f'Deletion of task "{task_title}" cancelled.'
  return _confirm_preview(question, details, cancel_message)


# --- Graph nodes --- #
def session_initialiser_node(state: AgentState) -> dict:
  if not config.briefing_enabled or state.get('briefing_shown', False):
    return { 'briefing_shown': True }

  system_prompt = (
    'You are a session initialiser for a personal assistant agent. '
    'Provide the user with a daily briefing of their tasks. '
    'Use the get_daily_briefing_data tool to retrieve structured task data, ' \
    'then format it into a concise message using the format_task_preview tool. '
    'Also suggest new dates for overdue and unscheduled tasks to help the user plan their day'
  )

  messages = [SystemMessage(content=system_prompt), *state['messages']]
  llm_with_tools = config.llm.bind_tools(tools.BRIEFING_TOOLS)
  response = llm_with_tools.invoke(messages)
  sanitized = _sanitize_tool_calls(response)
  return { 'messages': [sanitized] }

def after_initialiser_node(state: AgentState) -> dict:
  _ = state
  return { 'briefing_shown': True }

def intent_classifier_node(state: AgentState) -> dict:
  messages = [
    SystemMessage(
      content=(
        'You are an intent classifier for a personal assistant agent. '
        'Reply with only one word to reflect the user intent: '
        'task_create, task_read, task_update.'
        'If the intent is not clear, reply with unknown.'
      )
    ),
    *state['messages'],
  ]
  response = config.llm.invoke(messages)
  intent = _parse_intent(getattr(response, 'content', None))
  if intent == 'unknown':
    return {
      'messages': [
        AIMessage(content=(
          'Sorry, I could not understand your intent. '
          'Please clarify if you want to create, read, or update tasks.'
        ))
      ],
      'intent': intent
    }

  return { 'intent': intent }

def task_read_node(state: AgentState) -> dict:
  system_prompt = (
    'You are a task query assistant. Only read or list tasks; never create, update, or delete. '
    'Always use a filter builder tool before calling list_tasks. '
    'Be concise and return only task-related results using the user-facing format. '
    'Only use the information in the messages to build your query; '
    'do not make assumptions about unstated user preferences.'
  )
  messages = [SystemMessage(content=system_prompt), *state['messages']]
  llm_with_tools = config.llm.bind_tools(tools.TASK_READ_TOOLS)
  response = llm_with_tools.invoke(messages)
  sanitized = _sanitize_tool_calls(response)
  return { 'messages': [sanitized] }

def task_create_node(state: AgentState) -> dict:
  system_prompt = (
    'You are a task creation assistant. Gather the required title and any optional fields. '
    'Never parse dates yourself; always use the tools for that. '
    'Always use the user-facing format for showing task details.'
  )
  messages = [SystemMessage(content=system_prompt), *state['messages']]
  llm_with_tools = config.llm.bind_tools(tools.TASK_CREATE_TOOLS)
  response = llm_with_tools.invoke(messages)
  sanitized = _sanitize_tool_calls(response)
  return {
    'messages': [sanitized],
    'confirmation': None,
    'cancelled': None
  }

def task_update_node(state: AgentState) -> dict:
  system_prompt = (
    'You are a task update and delete/cancel assistant. '
    'Identify the target task first using get_task or list_tasks. '
    'If multiple tasks match, ask the user to clarify which one. '
    'Never parse dates yourself; always use the tools for that. '
    'Only use parse_date_range for filters, never for updating task fields. '
    'Always use the user-facing format for showing task details.'
  )
  messages = [SystemMessage(content=system_prompt), *state['messages']]
  llm_with_tools = config.llm.bind_tools(tools.TASK_UPDATE_TOOLS)
  response = llm_with_tools.invoke(messages)
  sanitized = _sanitize_tool_calls(response)
  return {
    'messages': [sanitized],
    'confirmation': None,
    'cancelled': None
  }

def task_interrupt_node(state: AgentState) -> dict:
  tool_calls = [
    msg.tool_calls[0] for msg in state['messages']
    if isinstance(msg, AIMessage) and msg.tool_calls
  ]
  target_call = next(
    (
      call for call in reversed(tool_calls)
      if call['name'] in {'create_task', 'update_task', 'delete_task'}
    ),
    None
  )

  if target_call is None:
    return {
      'messages': [AIMessage(content='No actionable tool call found. Please clarify your request.')]
    }

  handler = {
    'create_task': _handle_create_interrupt,
    'update_task': _handle_update_interrupt,
    'delete_task': _handle_delete_interrupt
  }.get(target_call['name'])

  return handler(target_call)
