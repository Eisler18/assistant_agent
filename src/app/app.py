from uuid import uuid4

import gradio as gr

from .graph_runner import TurnResult, invoke_turn, resume_turn
from .formatting import to_gradio_messages, format_interrupt_label

def _handle_turn_result(result: TurnResult) -> tuple[list[dict], bool]:
  messages = to_gradio_messages(result.messages)
  if result.is_interrupted:
    messages.append(
      { 'role': 'assistant', 'content': format_interrupt_label(result.interrupt_payload) }
    )

  return messages[1:], result.is_interrupted

def handle_user_message(user_text: str, history: list[dict]) -> tuple[list[dict], str]:
  if (user_text or '').strip() == '':
    return history, user_text
  history = history + [{ 'role': 'user', 'content': user_text } ]
  return history, ''

def handle_ai_response(history: list[dict], state: dict):
  if not history or history[-1].get('role') != 'user':
    return history, state, gr.update(visible=False)

  if not state.get('thread_id', False):
    state['thread_id'] = str(uuid4())

  user_text = history[-1]['content'][-1]['text']

  if state.get('is_interrupted'):
    result = resume_turn(user_text, state['thread_id'])
  else:
    result = invoke_turn(user_text, state['thread_id'], {})

  messages, is_interrupted = _handle_turn_result(result)
  state['is_interrupted'] = is_interrupted
  return messages, state, gr.update(visible=is_interrupted)

def _handle_button_response(value: str, _history: list[dict], state: dict):
  if not state.get('thread_id', False):
    state['thread_id'] = str(uuid4())

  result = resume_turn(value, state['thread_id'])

  messages, is_interrupted = _handle_turn_result(result)
  state['is_interrupted'] = is_interrupted

  return messages, state, gr.update(visible=is_interrupted)

def handle_yes(history: list[dict], state: dict):
  return _handle_button_response('yes', history, state)

def handle_no(history: list[dict], state: dict):
  return _handle_button_response('no', history, state)

def on_session_start(state: dict):
  state['thread_id'] = str(uuid4())

  result = invoke_turn('Generate a daily briefing of my tasks', state['thread_id'])

  messages, is_interrupted = _handle_turn_result(result)
  state['is_interrupted'] = is_interrupted

  return messages, state, gr.update(visible=is_interrupted)

def build_app() -> gr.Blocks:
  with gr.Blocks(title='Time Management Assistant') as demo:
    session_state = gr.State(
      { 'thread_id': None, 'is_interrupted': False }
    )

    chatbot = gr.Chatbot(label='Assistant', height=500)

    with gr.Group(visible=False) as interrupt_group:
      with gr.Row():
        yes_btn = gr.Button('Confirm', variant='primary')
        no_btn = gr.Button('Cancel', variant='stop')

    with gr.Row():
      msg_box = gr.Textbox(placeholder='Type a message...', show_label=False, scale=9)
      send_btn = gr.Button('Send', scale=1)

    send_btn.click(
      fn=handle_user_message,
      inputs=[msg_box, chatbot],
      outputs=[chatbot, msg_box]
    ).then(
      fn=handle_ai_response,
      inputs=[chatbot, session_state],
      outputs=[chatbot, session_state, interrupt_group]
    )
    msg_box.submit(
      fn=handle_user_message,
      inputs=[msg_box, chatbot],
      outputs=[chatbot, msg_box]
    ).then(
      fn=handle_ai_response,
      inputs=[chatbot, session_state],
      outputs=[chatbot, session_state, interrupt_group]
    )

    yes_btn.click(
      fn=handle_yes,
      inputs=[chatbot, session_state],
      outputs=[chatbot, session_state, interrupt_group]
    )

    no_btn.click(
      fn=handle_no,
      inputs=[chatbot, session_state],
      outputs=[chatbot, session_state, interrupt_group]
    )

    demo.load(
      fn=on_session_start,
      inputs=[session_state],
      outputs=[chatbot, session_state, interrupt_group]
    )

  return demo
