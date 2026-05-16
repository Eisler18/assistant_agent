
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END
import pytest

from assistant_agent.graph.nodes import intent_classifier_node, task_read_node
from assistant_agent.graph.graph import should_continue
from assistant_agent.config import Config

@pytest.fixture(name='fake_llm')
def llm(monkeypatch):
  # pylint: disable=arguments-differ
  class FakeLLM(GenericFakeChatModel):
    def bind_tools(self, tools):
      return self
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
  def test_task_read_node_returns_message(self, fake_llm):
    fake_llm.messages = iter([AIMessage(content='Here are your tasks')])
    state = {
      'messages': [HumanMessage(content='Show tasks')],
      'intent': 'task_read'
    }
    result = task_read_node(state)

    assert result['messages'][0].content == 'Here are your tasks'

  def test_task_read_routes_to_tools_when_tool_calls_present(self, fake_llm):
    fake_llm.messages = iter([
      AIMessage(content='Example', tool_calls=[{'name': 'tool', 'args': {}, 'id': '1'}])
    ])
    state = {
      'messages': [
        AIMessage(
          content='Example',
          tool_calls=[{'name': 'tool', 'args': {}, 'id': '1'}]
        )
      ],
      'intent': 'task_read'
    }

    assert should_continue(state) == 'task_read_tools'

  def test_task_read_routes_to_end_without_tool_calls(self, fake_llm):
    fake_llm.messages = iter([AIMessage(content='Done')])
    state = {
      'messages': [AIMessage(content='Done')],
      'intent': 'task_read'
    }

    assert should_continue(state) == END
