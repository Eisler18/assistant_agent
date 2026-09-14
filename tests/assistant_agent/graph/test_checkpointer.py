
import os
import uuid

import psycopg
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage

from assistant_agent.config import Config
from assistant_agent.graph.checkpointer import build_checkpointer
from assistant_agent.graph.graph import build_graph

TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL')

pytestmark = pytest.mark.integration

requires_test_db = pytest.mark.skipif(
  not TEST_DATABASE_URL,
  reason='TEST_DATABASE_URL is not set; skipping Postgres checkpointer integration tests'
)

@pytest.fixture(name='schema_url')
def fixture_schema_url():
  schema = f'test_checkpoints_{uuid.uuid4().hex}'

  with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as conn:
    conn.execute(f'CREATE SCHEMA "{schema}"')

  yield f'{TEST_DATABASE_URL}?options=-csearch_path%3D{schema}'

  with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as conn:
    conn.execute(f'DROP SCHEMA "{schema}" CASCADE')


@requires_test_db
def test_graph_state_survives_across_separate_instances(schema_url, monkeypatch):
  fake_llm = GenericFakeChatModel(
    messages=iter([AIMessage(content='unknown'), AIMessage(content='unknown')])
  )
  monkeypatch.setattr(Config, 'llm', fake_llm)
  monkeypatch.setattr('assistant_agent.graph.nodes.config._briefing_enabled', False)

  thread_config = { 'configurable': { 'thread_id': 'integration-thread' } }

  first_graph = build_graph(build_checkpointer(schema_url))
  first_graph.invoke(
    { 'messages': [HumanMessage(content='Hello')], 'intent': 'unknown' },
    config=thread_config
  )

  second_graph = build_graph(build_checkpointer(schema_url))
  result = second_graph.invoke(
    { 'messages': [HumanMessage(content='And tomorrow?')], 'intent': 'unknown' },
    config=thread_config
  )

  message_text = [
    message.content for message in result['messages'] if isinstance(message, HumanMessage)
  ]
  assert message_text == ['Hello', 'And tomorrow?']

def test_in_memory_checkpointer_is_used(monkeypatch):
  fake_llm = GenericFakeChatModel(
    messages=iter([AIMessage(content='unknown'), AIMessage(content='unknown')])
  )
  monkeypatch.setattr(Config, 'llm', fake_llm)
  monkeypatch.setattr('assistant_agent.graph.nodes.config._briefing_enabled', False)

  thread_config = { 'configurable': { 'thread_id': 'integration-thread' } }

  first_graph = build_graph(build_checkpointer(None))
  first_graph.invoke(
    { 'messages': [HumanMessage(content='Hello')], 'intent': 'unknown' },
    config=thread_config
  )

  second_graph = build_graph(build_checkpointer(None))
  result = second_graph.invoke(
    { 'messages': [HumanMessage(content='And tomorrow?')], 'intent': 'unknown' },
    config=thread_config
  )

  message_text = [
    message.content for message in result['messages'] if isinstance(message, HumanMessage)
  ]
  assert message_text == ['And tomorrow?']
