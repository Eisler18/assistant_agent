
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END
import pytest

from assistant_agent.graph.react_agent import (
  react_agent,
  react_agent_node,
  should_continue,
  should_save
)
from assistant_agent.graph.state import AgentState
from assistant_agent.config import Config

# pylint: disable=duplicate-code
@pytest.fixture(name='fake_llm')
def llm(monkeypatch):
  # pylint: disable=arguments-differ
  class FakeLLM(GenericFakeChatModel):
    def __init__(self, messages):
      super().__init__(messages=messages)
      self._tools = []

    def bind_tools(self, tools):
      self._tools = tools
      return self

    def get_tools(self):
      return self._tools
  # pylint: enable=arguments-differ

  fake_llm = FakeLLM(messages=iter([]))
  monkeypatch.setattr(Config, 'llm', fake_llm)
  return fake_llm
# pylint: enable=duplicate-code

# ------------------------------------------------------------------ #
# Agent tests                                                        #
# ------------------------------------------------------------------ #
def test_graph_compiles():
  assert react_agent is not None

def test_graph_nodes_present():
  graph_def = react_agent.get_graph()
  node_names = set(graph_def.nodes.keys())

  assert 'react_agent' in node_names
  assert 'tools' in node_names
  assert 'task_interrupt' in node_names


# ------------------------------------------------------------------ #
# Routing tests                                                      #
# ------------------------------------------------------------------ #
def test_should_continue():
  read_task = AgentState(
    messages=[AIMessage(content='Example', tool_calls=[{'name': 'tool', 'args': {}, 'id': '1'}])]
  )
  assert should_continue(read_task) == 'tools'

  create_task_without_confirmation = AgentState(
    messages=[
      AIMessage(content='Example', tool_calls=[{'name': 'create_task', 'args': {}, 'id': '1'}])
    ]
  )
  assert should_continue(create_task_without_confirmation) == 'task_interrupt'

  create_task_with_confirmation = AgentState(
    messages=[
      AIMessage(content='Example', tool_calls=[{'name': 'create_task', 'args': {}, 'id': '1'}])
    ],
    confirmation=True
  )
  assert should_continue(create_task_with_confirmation) == 'tools'

  no_tool_state = AgentState(messages=[], intent='task_read')
  assert should_continue(no_tool_state) == END

def test_should_save_task():
  state = AgentState(messages=[], confirmation=True)
  assert should_save(state) == 'tools'

  state = AgentState(messages=[], confirmation=False)
  assert should_save(state) == 'react_agent'

  state = AgentState(messages=[], cancelled=True)
  assert should_save(state) == END


# ------------------------------------------------------------------ #
# Checkpointer tests                                                 #
# ------------------------------------------------------------------ #
def test_memory_saver_retains_messages(fake_llm):
  fake_llm.messages = iter([AIMessage(content='unknown'), AIMessage(content='unknown')])

  thread_config = { 'configurable': { 'thread_id': 'test-thread' } }

  first_state = {
    'messages': [HumanMessage(content='Hello')]
  }
  second_state = {
    'messages': [HumanMessage(content='And tomorrow?')]
  }

  react_agent.invoke(first_state, config=thread_config)
  result = react_agent.invoke(second_state, config=thread_config)

  message_text = [
    message.content for message in result['messages'] if isinstance(message, HumanMessage)
  ]
  assert message_text == ['Hello', 'And tomorrow?']

# ------------------------------------------------------------------ #
# Agent Node tests                                                   #
# ------------------------------------------------------------------ #
class TestReactAgentNode:
  def test_react_agent_has_tools(self, fake_llm):
    fake_llm.messages = iter([AIMessage(content='task_read')])
    state = {
      'messages': [HumanMessage(content='What are my tasks for today?')]
    }

    _ = react_agent_node(state)

    tools = fake_llm.get_tools()
    tool_names = {tool.name for tool in tools}
    expected_names = {
      'create_task',
      'list_tasks',
      'format_task_preview',
      'build_overdue_filter',
      'delete_task',
      'parse_date_range',
      'get_daily_briefing_data',
      'build_unscheduled_filter',
      'update_task',
      'build_stale_filter',
      'get_task',
      'new_task',
      'build_today_filter',
      'generate_calendar_link'
    }

    assert expected_names == tool_names

  def test_react_agent_node_returns_message(self, fake_llm):
    fake_llm.messages = iter([AIMessage(content='New task created')])
    state = {
      'messages': [HumanMessage(content='Create a new task')]
    }
    result = react_agent_node(state)

    assert 'messages' in result
    assert result['messages'][0].content == 'New task created'

  def test_react_agent_sanitizes_tool_call_names(self, fake_llm):
    fake_llm.messages = iter([
      AIMessage(
        content='Example',
        tool_calls=[{'name': 'update_task<|channel|>json', 'args': {}, 'id': '1'}]
      )
    ])
    state = {
      'messages': [HumanMessage(content='Update a task')],
      'intent': 'task_read'
    }

    result = react_agent_node(state)

    assert result['messages'][0].tool_calls[0]['name'] == 'update_task'
