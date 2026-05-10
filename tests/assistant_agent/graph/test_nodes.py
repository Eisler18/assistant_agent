
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage


from assistant_agent.graph.nodes import intent_classifier_node
from assistant_agent.config import Config

# ------------------------------------------------------------------ #
# Intent classifier node tests                                       #
# ------------------------------------------------------------------ #
def test_intent_classifier_sets_task_crud(monkeypatch):
  fake_llm = GenericFakeChatModel(messages=iter([AIMessage(content='task_crud')]))
  monkeypatch.setattr(Config, 'llm', fake_llm)

  state = {'messages': [HumanMessage(content='Add a task for tomorrow')], 'intent': 'unknown'}

  result = intent_classifier_node(state)

  assert result['intent'] == 'task_crud'

def test_intent_classifier_defaults_to_unknown(monkeypatch):
  fake_llm = GenericFakeChatModel(messages=iter([AIMessage(content='Hi')]))
  monkeypatch.setattr(Config, 'llm', fake_llm)

  state = {'messages': [HumanMessage(content='Hello')], 'intent': 'unknown'}

  result = intent_classifier_node(state)

  assert result['intent'] == 'unknown'
