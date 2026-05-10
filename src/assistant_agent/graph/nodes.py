
from langchain_core.messages import AIMessage, SystemMessage

from assistant_agent.config import Config
from .state import AgentState

config = Config()

# --- Helper functions --- #
def _parse_intent(content: object) -> str:
  if isinstance(content, str):
    intent = content.strip()
    if intent in { 'task_crud', 'briefing', 'unknown' }:
      return intent
  return 'unknown'

# --- Graph nodes --- #
def intent_classifier_node(state: AgentState) -> dict:
  messages = [
    SystemMessage(
      content=(
        'You are an intent classifier for a personal assistant agent. '
        'Reply with only one word to reflect the user intent: task_crud, briefing, unknown.'
      )
    ),
    *state['messages'],
  ]
  response = config.llm.invoke(messages)
  return { 'intent': _parse_intent(getattr(response, 'content', None)) }

def task_crud_node(state: AgentState) -> dict:
  _ = state
  return {'messages': [AIMessage(content='[task_crud stub]')]}

def briefing_node(state: AgentState) -> dict:
  _ = state
  return {'messages': [AIMessage(content='[briefing stub]')]}
