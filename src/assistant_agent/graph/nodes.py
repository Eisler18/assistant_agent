
from typing import get_args
from langchain_core.messages import AIMessage, SystemMessage

from ..config import Config
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

# --- Graph nodes --- #
def intent_classifier_node(state: AgentState) -> dict:
  messages = [
    SystemMessage(
      content=(
        'You are an intent classifier for a personal assistant agent. '
        'Reply with only one word to reflect the user intent: '
        'task_create, task_read, task_update, task_delete.'
        'If the intent is not clear, reply with unknown.'
      )
    ),
    *state['messages'],
  ]
  response = config.llm.invoke(messages)
  return { 'intent': _parse_intent(getattr(response, 'content', None)) }

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
  _ = state
  return { 'messages': [AIMessage(content='[task_create stub]')] }

def task_update_node(state: AgentState) -> dict:
  _ = state
  return { 'messages': [AIMessage(content='[task_update stub]')] }

def task_delete_node(state: AgentState) -> dict:
  _ = state
  return { 'messages': [AIMessage(content='[task_delete stub]')] }
