
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
    'Be concise and return only task-related results.'
  )
  messages = [SystemMessage(content=system_prompt), *state['messages']]
  llm_with_tools = config.llm.bind_tools(tools.TASK_READ_TOOLS)
  response = llm_with_tools.invoke(messages)
  return { 'messages': [response] }

def task_create_node(state: AgentState) -> dict:
  _ = state
  return { 'messages': [AIMessage(content='[task_create stub]')] }

def task_update_node(state: AgentState) -> dict:
  _ = state
  return { 'messages': [AIMessage(content='[task_update stub]')] }

def task_delete_node(state: AgentState) -> dict:
  _ = state
  return { 'messages': [AIMessage(content='[task_delete stub]')] }
