
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import ToolException
import pytest

from assistant_agent.graph.nodes import (
  intent_classifier_node,
  task_interrupt_node,
  task_create_node,
  task_read_node,
  task_update_node
)
from assistant_agent.config import Config

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

# ------------------------------------------------------------------ #
# Intent classifier node tests                                       #
# ------------------------------------------------------------------ #
class TestIntentClassifierNode:
  def test_intent_classifier_sets_task_read(self, fake_llm):
    fake_llm.messages = iter([AIMessage(content='task_read')])
    state = {
      'messages': [HumanMessage(content='What are my tasks for today?')],
      'intent': 'unknown'
    }

    result = intent_classifier_node(state)

    assert result['intent'] == 'task_read'

  def test_intent_classifier_defaults_to_unknown(self, fake_llm):
    fake_llm.messages = iter([AIMessage(content='Unclear response')])
    state = {
      'messages': [HumanMessage(content='Hello')],
      'intent': 'unknown'
    }

    result = intent_classifier_node(state)

    assert result['intent'] == 'unknown'

# ------------------------------------------------------------------ #
# Task read node tests                                               #
# ------------------------------------------------------------------ #
class TestTaskReadNode:
  def test_task_read_has_read_tools(self, fake_llm):
    fake_llm.messages = iter([AIMessage(content='task_read')])
    state = {
      'messages': [HumanMessage(content='What are my tasks for today?')],
      'intent': 'task_read'
    }

    _ = task_read_node(state)

    tools = fake_llm.get_tools()
    tool_names = {tool.name for tool in tools}
    expected_names = {
      'list_tasks',
      'format_task_preview',
      'build_overdue_filter',
      'parse_date_range',
      'build_unscheduled_filter',
      'get_task',
      'build_today_filter'
    }

    assert expected_names == tool_names

  def test_task_read_node_returns_message(self, fake_llm):
    fake_llm.messages = iter([AIMessage(content='Here are your tasks')])
    state = {
      'messages': [HumanMessage(content='Show tasks')],
      'intent': 'task_read'
    }
    result = task_read_node(state)

    assert 'messages' in result
    assert result['messages'][0].content == 'Here are your tasks'

  def test_task_read_sanitizes_tool_call_names(self, fake_llm):
    fake_llm.messages = iter([
      AIMessage(
        content='Example',
        tool_calls=[{'name': 'list_tasks<|channel|>json', 'args': {}, 'id': '1'}]
      )
    ])
    state = {
      'messages': [HumanMessage(content='Show tasks')],
      'intent': 'task_read'
    }

    result = task_read_node(state)

    assert result['messages'][0].tool_calls[0]['name'] == 'list_tasks'

# ------------------------------------------------------------------ #
# Task create node tests                                               #
# ------------------------------------------------------------------ #
class TestTaskCreateNode:
  def test_task_create_returns_message(self, fake_llm):
    fake_llm.messages = iter([
      AIMessage(content='Example', tool_calls=[{ 'name': 'new_task', 'args': {}, 'id': '1' }])
    ])
    state = {
      'messages': [HumanMessage(content='Create a task')],
      'intent': 'task_create'
    }

    result = task_create_node(state)

    assert result['messages'][0].tool_calls[0]['name'] == 'new_task'
    assert result['messages'][0].content == 'Example'

  def test_task_create_has_create_tools(self, fake_llm):
    fake_llm.messages = iter([AIMessage(content='Example')])
    state = {
      'messages': [HumanMessage(content='Create a task')],
      'intent': 'task_create'
    }

    _ = task_create_node(state)

    tools = fake_llm.get_tools()
    tool_names = {tool.name for tool in tools}
    expected_names = {
      'create_task',
      'new_task',
      'format_task_preview'
    }
    assert expected_names == tool_names

# ------------------------------------------------------------------ #
# Task update node tests                                             #
# ------------------------------------------------------------------ #
class TestTaskUpdateNode:
  def test_task_update_returns_message(self, fake_llm):
    fake_llm.messages = iter([
      AIMessage(content='Example', tool_calls=[{ 'name': 'update_task', 'args': {}, 'id': '1' }])
    ])
    state = {
      'messages': [HumanMessage(content='Update a task')],
      'intent': 'task_update'
    }

    result = task_update_node(state)

    assert result['messages'][0].tool_calls[0]['name'] == 'update_task'
    assert result['messages'][0].content == 'Example'

  def test_task_update_has_update_tools(self, fake_llm):
    fake_llm.messages = iter([AIMessage(content='Example')])
    state = {
      'messages': [HumanMessage(content='Update a task')],
      'intent': 'task_update'
    }

    _ = task_update_node(state)

    tools = fake_llm.get_tools()
    tool_names = {tool.name for tool in tools}
    expected_names = {
      'get_task',
      'list_tasks',
      'update_task',
      'parse_date_range',
      'format_task_preview'
    }
    assert expected_names == tool_names

# ------------------------------------------------------------------ #
# Task interrupt node tests                                          #
# ------------------------------------------------------------------ #
class TestTaskInterruptNode:
  def test_task_interrupt_returns_confirmation(self, monkeypatch):
    monkeypatch.setattr('assistant_agent.graph.nodes.interrupt', lambda _: 'yes')
    state = {
      'messages': [
        HumanMessage(content='Create a task'),
        AIMessage(
          content='',
          tool_calls=[
            {
              'name': 'create_task',
              'args': {
                'title': 'Test Task'
              },
              'id': '1'
            }
          ]
        )
      ],
      'intent': 'task_create'
    }

    result = task_interrupt_node(state)

    assert result['confirmation'] is True
    assert 'cancelled' not in result
    assert 'messages' not in result

  def test_task_interrupt_returns_cancellation(self, monkeypatch):
    monkeypatch.setattr('assistant_agent.graph.nodes.interrupt', lambda _: 'No, I changed my mind.')
    state = {
      'messages': [
        HumanMessage(content='Create a task'),
        AIMessage(
          content='',
          tool_calls=[
            {
              'name': 'create_task',
              'args': {
                'title': 'Test Task'
              },
              'id': '1'
            }
          ]
        )
      ],
      'intent': 'task_create'
    }

    result = task_interrupt_node(state)

    assert result['cancelled'] is True
    assert result['messages'][0].content == 'Task creation cancelled.'
    assert 'confirmation' not in result

  def test_task_interrupt_returns_details(self, monkeypatch):
    monkeypatch.setattr(
      'assistant_agent.graph.nodes.interrupt',
      lambda _: 'I want to change the date'
    )
    state = {
      'messages': [
        HumanMessage(content='Create a task'),
        AIMessage(
          content='',
          tool_calls=[
            {
              'name': 'create_task',
              'args': {
                'title': 'Test Task'
              },
              'id': '1'
            }
          ]
        )
      ],
      'intent': 'task_create'
    }

    result = task_interrupt_node(state)

    assert 'confirmation' not in result
    assert 'cancelled' not in result
    assert result['messages'][0].content == 'I want to change the date'

  def test_task_interrupt_update_confirmation(self, monkeypatch):
    class FakeTool():
      def invoke(self, _query: str) -> dict:
        return self.run(_query)

      def run(self, _query: str) -> str:
        return { 'tasks': [{ 'title': 'Test Task' }] }

    monkeypatch.setattr('assistant_agent.graph.nodes.interrupt', lambda _: 'yes')
    monkeypatch.setattr('assistant_agent.graph.nodes.tools.get_task', FakeTool())

    state = {
      'messages': [
        HumanMessage(content='Update a task'),
        AIMessage(
          content='',
          tool_calls=[
            {
              'name': 'update_task',
              'args': {
                'task_id': '123',
                'title': 'Updated title'
              },
              'id': '1'
            }
          ]
        )
      ],
      'intent': 'task_update'
    }

    result = task_interrupt_node(state)

    assert result['confirmation'] is True
    assert 'cancelled' not in result
    assert 'messages' not in result

  def test_task_interrupt_update_missing_task_id(self):
    state = {
      'messages': [
        HumanMessage(content='Update a task'),
        AIMessage(
          content='',
          tool_calls=[
            {
              'name': 'update_task',
              'args': {
                'title': 'Updated title'
              },
              'id': '1'
            }
          ]
        )
      ],
      'intent': 'task_update'
    }

    with pytest.raises(
      ToolException,
      match='Failed to retrieve current task details for task_id: None'
    ):
      task_interrupt_node(state)
