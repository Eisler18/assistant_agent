from langchain_core.messages import HumanMessage, AIMessage

from app.formatting import to_gradio_messages, format_interrupt_label

# --------------------------------------------------------------- #
# Test messages conversion to Gradio format                       #
# --------------------------------------------------------------- #
def test_human_message_converted():
  msgs = [HumanMessage(content='Hello')]
  out = to_gradio_messages(msgs)
  assert out == [{ 'role': 'user', 'content': 'Hello' }]

def test_ai_message_with_content_converted():
  msgs = [AIMessage(content='Reply')]
  out = to_gradio_messages(msgs)
  assert out == [{ 'role': 'assistant', 'content': 'Reply' }]

def test_ai_message_with_only_tool_calls_skipped():
  m = AIMessage(
    content='',
    tool_calls=[
      {
        'name': 'delete_task',
        'args': { 'task_id': '567' },
        'id': '1'
      }
    ]
  )
  out = to_gradio_messages([m])
  assert not out

def test_mixed_messages_produces_expected_output():
  a = HumanMessage(content='User')
  b = AIMessage(content='Assistant reply')
  c = AIMessage(
    content='',
    tool_calls=[{
      'name': 'do_it',
      'args': {},
      'id': '1'
    }]
  )

  out = to_gradio_messages([a, c, b])
  assert out == [
    {'role': 'user', 'content': 'User'},
    {'role': 'assistant', 'content': 'Assistant reply'},
  ]

# --------------------------------------------------------------- #
# Test interrupt label formatting                                 #
# --------------------------------------------------------------- #
def test_format_interrupt_label():
  payload = { 'question': 'Proceed?', 'details': 'This will delete' }
  s = format_interrupt_label(payload)
  assert '⚠️ Confirmation required' in s
  assert 'This will delete' in s
  assert 'Proceed?' in s

def test_format_interrupt_label_no_payload():
  s = format_interrupt_label(None)
  assert s == '⚠️ Confirmation required'
