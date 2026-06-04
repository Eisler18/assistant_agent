from typing import Iterable

from langchain_core.messages import HumanMessage, AIMessage

def to_gradio_messages(messages: Iterable[object]) -> list[dict]:
  out: list[dict] = []
  for message in messages:
    if isinstance(message, HumanMessage):
      out.append({ 'role': 'user', 'content': message.content })

    elif isinstance(message, AIMessage):
      content = (message.content or '').strip()

      if not content or bool(getattr(message, 'tool_calls', None)):
        continue

      out.append({ 'role': 'assistant', 'content': content })

  return out


def format_interrupt_label(payload: dict | None) -> str:
  base = '⚠️ Confirmation required'
  if not payload:
    return base

  details = payload.get('details', '')
  question = payload.get('question', '')

  parts = [base]
  if details:
    parts.append('')
    parts.append(details)
  if question:
    parts.append('')
    parts.append(question)

  return '\n'.join(parts)
