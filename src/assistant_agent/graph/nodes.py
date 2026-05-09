
from langchain_core.messages import AIMessage
from .state import AgentState

def intent_classifier_node(state: AgentState) -> dict:
  _ = state
  return { 'intent': 'unknown' }

def task_crud_node(state: AgentState) -> dict:
  _ = state
  return { 'messages': [AIMessage(content='[task_crud stub]')] }

def briefing_node(state: AgentState) -> dict:
  _ = state
  return { 'messages': [AIMessage(content='[briefing stub]')] }
