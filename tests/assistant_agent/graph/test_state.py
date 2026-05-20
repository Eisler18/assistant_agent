
from typing import get_args
from langchain_core.messages import HumanMessage
from langgraph.graph.message import add_messages
from assistant_agent.graph.state import AgentState, IntentType

class TestAgentState:
  def test_agent_state_instantiation(self):
    state: AgentState = {
      'messages': [HumanMessage(content='Hi', id='1')],
      'intent': 'unknown'
    }

    assert state['intent'] == 'unknown'

  def test_add_messages_merges_by_id(self):
    first = HumanMessage(content='First', id='1')
    second = HumanMessage(content='Second', id='1')

    merged = add_messages([first], [second])

    assert len(merged) == 1
    assert merged[0].content == 'Second'

    third = HumanMessage(content='Third', id='2')
    merged = add_messages(merged, [third])

    assert len(merged) == 2
    assert merged[0].content == 'Second'
    assert merged[1].content == 'Third'

  def test_intent_literals_match_routes(self):
    intents = set(get_args(IntentType))

    assert len(intents) == 4
    assert 'unknown' in intents
    assert all(intent.startswith('task_') or intent == 'unknown' for intent in intents)
