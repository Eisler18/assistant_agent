from types import SimpleNamespace
from langchain_core.messages import AIMessage, HumanMessage

from evaluation import trace

def test_extract_tool_calls():
  messages = [HumanMessage(content='Hello')]
  assert not trace.extract_tool_calls(messages)

  messages = [
    AIMessage(
      content='step',
      tool_calls=[
        {'name': 'tool_a', 'args': {}, 'id': '1'},
        {'name': 'tool_b', 'args': {}, 'id': '2'}
      ]
    ),
    AIMessage(content='next', tool_calls=[{'name': 'tool_c', 'args': {}, 'id': '3'}])
  ]
  assert trace.extract_tool_calls(messages) == ['tool_a', 'tool_b', 'tool_c']

def test_interrupt_was_fired():
  assert trace.interrupt_was_fired(SimpleNamespace(interrupts=['stop'])) is True
  assert trace.interrupt_was_fired(SimpleNamespace(interrupts=[])) is False

def test_get_last_ai_message_content():
  messages = [
    HumanMessage(content='User'),
    AIMessage(content='First'),
    HumanMessage(content='User again'),
    AIMessage(content='Last')
  ]
  assert trace.get_last_ai_message_content(messages) == 'Last'

  assert trace.get_last_ai_message_content([HumanMessage(content='Only user')]) == ''
