from langchain_core.messages import AIMessage

def extract_tool_calls(messages: list) -> list[str]:
  calls: list[str] = []
  for message in messages:
    if isinstance(message, AIMessage) and message.tool_calls:
      calls.extend(call['name'] for call in message.tool_calls)
  return calls

def interrupt_was_fired(result) -> bool:
  return bool(getattr(result, 'interrupts', []))

def get_last_ai_message_content(messages: list) -> str:
  for message in reversed(messages):
    if isinstance(message, AIMessage):
      return message.content or ''
  return ''
