
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END

from assistant_agent.graph.graph import graph, route_by_intent, should_continue
from assistant_agent.graph.state import AgentState

# ------------------------------------------------------------------ #
# Helper functions                                                   #
# ------------------------------------------------------------------ #
def sample_state(messages: list[BaseMessage], intent: str | None) -> AgentState:
  return AgentState(messages=messages, intent=intent)

# ------------------------------------------------------------------ #
# Graph tests                                                        #
# ------------------------------------------------------------------ #
def test_graph_compiles():
  assert graph is not None

def test_graph_nodes_present():
  graph_def = graph.get_graph()
  node_names = set(graph_def.nodes.keys())

  assert 'intent_classifier' in node_names
  assert 'task_crud' in node_names
  assert 'briefing' in node_names
  assert 'task_tools' in node_names
  assert 'briefing_tools' in node_names


# ------------------------------------------------------------------ #
# Routing tests                                                      #
# ------------------------------------------------------------------ #
def test_route_by_intent():
  task_crud_state = sample_state(messages=[], intent='task_crud')
  assert route_by_intent(task_crud_state) == 'task_crud'

  briefing_state = sample_state(messages=[], intent='briefing')
  assert route_by_intent(briefing_state) == 'briefing'

  unknown_state = sample_state(messages=[], intent=None)
  assert route_by_intent(unknown_state) == END

def test_should_continue():
  task_crud_state = sample_state(
    messages=[AIMessage(content='Example', tool_calls=[{'name': 'tool', 'args': {}, 'id': '1'}])],
    intent='task_crud'
  )
  assert should_continue(task_crud_state) == 'task_tools'

  briefing_state = sample_state(
    messages=[AIMessage(content='Example', tool_calls=[{'name': 'tool', 'args': {}, 'id': '1'}])],
    intent='briefing'
  )
  assert should_continue(briefing_state) == 'briefing_tools'

  no_intent_state = sample_state(
    messages=[AIMessage(content='Example', tool_calls=[{'name': 'tool', 'args': {}, 'id': '1'}])],
    intent=None
  )
  assert should_continue(no_intent_state) == END

  no_tool_state = sample_state(messages=[], intent='task_crud')
  assert should_continue(no_tool_state) == END
