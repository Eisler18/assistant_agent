import os
from dataclasses import dataclass

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.types import Command
from langgraph.graph import StateGraph

from assistant_agent.graph.react_agent import react_agent
from assistant_agent.graph.graph import graph
from assistant_agent.repository import JsonRepository
from assistant_agent.models import Task
from assistant_agent.graph.state import AgentState

@dataclass
class TurnResult:
  messages: list[BaseMessage]
  is_interrupted: bool
  interrupt_payload: dict | None = None


def _get_graph() -> StateGraph:
  if os.getenv('AGENT_GRAPH', '').lower() == 'react':
    return react_agent

  return graph

def _setup_repository() -> None:
  repo = JsonRepository(file_name='tasks.json')
  Task.set_repository(repo)

def _extract_turn_result(result: AgentState) -> TurnResult:
  interrupts = getattr(result, 'interrupts', []) or []
  is_interrupted = bool(interrupts)
  interrupt_payload = None
  if is_interrupted:
    first = interrupts[0]
    interrupt_payload = getattr(first, 'value', None)

  value = getattr(result, 'value', {}) or {}
  messages = value.get('messages', [])
  return TurnResult(
    messages=messages,
    is_interrupted=is_interrupted,
    interrupt_payload=interrupt_payload,
  )

_setup_repository()

def invoke_turn(user_input: str, thread_id: str, initial_state: dict | None = None) -> TurnResult:
  state = initial_state or {}
  state.setdefault('messages', []).append(HumanMessage(content=user_input))

  system = _get_graph()
  result = system.invoke(
    state,
    config={ 'configurable': { 'thread_id': thread_id } },
    version='v2'
  )
  return _extract_turn_result(result)


def resume_turn(value: str, thread_id: str) -> TurnResult:
  system = _get_graph()
  result = system.invoke(
    Command(resume=value),
    config={ 'configurable': { 'thread_id': thread_id } },
    version='v2',
  )

  return _extract_turn_result(result)
