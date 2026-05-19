
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END

from assistant_agent.graph.graph import graph, route_by_intent, should_continue, should_save_task
from assistant_agent.graph.state import AgentState
from assistant_agent.config import Config

# ------------------------------------------------------------------ #
# Graph tests                                                        #
# ------------------------------------------------------------------ #
def test_graph_compiles():
  assert graph is not None

def test_graph_nodes_present():
  graph_def = graph.get_graph()
  node_names = set(graph_def.nodes.keys())

  assert 'intent_classifier' in node_names
  assert 'task_read' in node_names
  assert 'task_read_tools' in node_names
  assert 'task_create' in node_names
  assert 'task_interrupt' in node_names
  assert 'task_create_tools' in node_names
  assert 'task_update' in node_names
  assert 'task_update_tools' in node_names


# ------------------------------------------------------------------ #
# Routing tests                                                      #
# ------------------------------------------------------------------ #
def test_route_by_intent():
  task_read_state = AgentState(messages=[], intent='task_read')
  assert route_by_intent(task_read_state) == 'task_read'

  task_create_state = AgentState(messages=[], intent='task_create')
  assert route_by_intent(task_create_state) == 'task_create'

  unknown_state = AgentState(messages=[], intent=None)
  assert route_by_intent(unknown_state) == END

def test_should_continue():
  task_read_state = AgentState(
    messages=[AIMessage(content='Example', tool_calls=[{'name': 'tool', 'args': {}, 'id': '1'}])],
    intent='task_read'
  )
  assert should_continue(task_read_state) == 'task_read_tools'

  task_create_state = AgentState(
    messages=[
      AIMessage(content='Example', tool_calls=[{'name': 'create_task', 'args': {}, 'id': '1'}])
    ],
    intent='task_create'
  )
  assert should_continue(task_create_state) == 'task_interrupt'

  task_create_state = AgentState(
    messages=[
      AIMessage(content='Example', tool_calls=[{'name': 'create_task', 'args': {}, 'id': '1'}])
    ],
    intent='task_create',
    confirmation=True
  )
  assert should_continue(task_create_state) == 'task_create_tools'

  task_create_state = AgentState(
    messages=[
      AIMessage(content='Example', tool_calls=[{'name': 'new_task', 'args': {}, 'id': '1'}])
    ],
    intent='task_create'
  )
  assert should_continue(task_create_state) == 'task_create_tools'

  task_update_state = AgentState(
    messages=[
      AIMessage(content='Example', tool_calls=[{'name': 'update_task', 'args': {}, 'id': '1'}])
    ],
    intent='task_update'
  )
  assert should_continue(task_update_state) == 'task_interrupt'

  task_update_state = AgentState(
    messages=[
      AIMessage(content='Example', tool_calls=[{'name': 'list_tasks', 'args': {}, 'id': '1'}])
    ],
    intent='task_update'
  )
  assert should_continue(task_update_state) == 'task_update_tools'

  task_delete_state = AgentState(
    messages=[
      AIMessage(content='Example', tool_calls=[{'name': 'delete_task', 'args': {}, 'id': '1'}])
    ],
    intent='task_update'
  )
  assert should_continue(task_delete_state) == 'task_interrupt'

  no_intent_state = AgentState(
    messages=[AIMessage(content='Example', tool_calls=[{'name': 'tool', 'args': {}, 'id': '1'}])],
    intent=None
  )
  assert should_continue(no_intent_state) == END

  no_tool_state = AgentState(messages=[], intent='task_read')
  assert should_continue(no_tool_state) == END

def test_should_save_task():
  state = AgentState(messages=[], intent='task_create', confirmation=True)
  assert should_save_task(state) == 'task_create_tools'

  state = AgentState(messages=[], intent='task_create', confirmation=False)
  assert should_save_task(state) == 'task_create'

  state = AgentState(messages=[], intent='task_create', cancelled=True)
  assert should_save_task(state) == END

  state = AgentState(messages=[], intent='task_read')
  assert should_save_task(state) == END

  state = AgentState(messages=[], intent='task_update', confirmation=True)
  assert should_save_task(state) == 'task_update_tools'

  state = AgentState(messages=[], intent='task_update', confirmation=False)
  assert should_save_task(state) == 'task_update'

  state = AgentState(messages=[], intent='task_update', cancelled=True)
  assert should_save_task(state) == END


# ------------------------------------------------------------------ #
# Checkpointer tests                                                 #
# ------------------------------------------------------------------ #
def test_memory_saver_retains_messages(monkeypatch):
  fake_llm = GenericFakeChatModel(
    messages=iter([AIMessage(content='unknown'), AIMessage(content='unknown')])
  )
  monkeypatch.setattr(Config, 'llm', fake_llm)

  thread_config = { 'configurable': { 'thread_id': 'test-thread' } }

  first_state = {
    'messages': [HumanMessage(content='Hello')],
    'intent': 'unknown'
  }
  second_state = {
    'messages': [HumanMessage(content='And tomorrow?')],
    'intent': 'unknown'
  }

  graph.invoke(first_state, config=thread_config)
  result = graph.invoke(second_state, config=thread_config)

  message_text = [message.content for message in result['messages']]
  assert message_text == ['Hello', 'And tomorrow?']
