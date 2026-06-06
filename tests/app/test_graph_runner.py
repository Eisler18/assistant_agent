from types import SimpleNamespace
from unittest.mock import MagicMock

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from app.graph_runner import _get_graph, invoke_turn, resume_turn

# ----------------------------------------------------- #
# Test get_graph behavior based on environment variable #
# ----------------------------------------------------- #
def test_get_graph_default(monkeypatch):
  monkeypatch.delenv('AGENT_GRAPH', raising=False)
  g = _get_graph()
  assert hasattr(g, 'invoke')

  monkeypatch.setenv('AGENT_GRAPH', 'react')
  g = _get_graph()
  assert hasattr(g, 'invoke')

# ----------------------------------------------------- #
# Test invoke_turn behavior                             #
# ----------------------------------------------------- #
def test_invoke_turn_normal(monkeypatch):
  fake_result = SimpleNamespace(
    interrupts=[],
    value={ 'messages': [HumanMessage(content='Hello'), AIMessage(content='Hi')] }
  )
  fake_graph = MagicMock()
  fake_graph.invoke.return_value = fake_result
  monkeypatch.setattr('app.graph_runner._get_graph', lambda: fake_graph)

  res = invoke_turn('Hello', 'thread-1')

  assert res.is_interrupted is False
  assert res.messages[-1].content == 'Hi'

  call_args = fake_graph.invoke.call_args
  state_arg = call_args[0][0]
  assert state_arg['messages'][-1].content == 'Hello'

def test_invoke_turn_interrupted(monkeypatch):
  payload = { 'question': 'Confirm?', 'details': 'Task: Write report' }
  fake_interrupt = SimpleNamespace(value=payload)
  fake_result = SimpleNamespace(
    interrupts=[fake_interrupt],
    value={ 'messages': [HumanMessage(content='Create task')] }
  )
  fake_graph = MagicMock()
  fake_graph.invoke.return_value = fake_result
  monkeypatch.setattr('app.graph_runner._get_graph', lambda: fake_graph)

  res = invoke_turn('Create task', 'thread-2')

  assert res.is_interrupted is True
  assert res.interrupt_payload == payload

# ----------------------------------------------------- #
# Test resume_turn behavior                             #
# ----------------------------------------------------- #
def test_resume_turn(monkeypatch):
  fake_result = SimpleNamespace(
    interrupts=[],
    value={ 'messages': [AIMessage(content='Task created')] }
  )
  fake_graph = MagicMock()
  fake_graph.invoke.return_value = fake_result
  monkeypatch.setattr('app.graph_runner._get_graph', lambda: fake_graph)

  res = resume_turn('yes', 'thread-3')

  assert res.is_interrupted is False

  call_args = fake_graph.invoke.call_args
  command_arg = call_args[0][0]
  assert isinstance(command_arg, Command)
  assert command_arg.resume == 'yes'
