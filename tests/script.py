from langchain_core.messages import HumanMessage
from langgraph.types import Command

from assistant_agent.graph.graph import graph
from assistant_agent.models import Task
from assistant_agent.repository import JsonRepository

def _print_last_message(messages: list) -> None:
  if not messages:
    print('No messages in state.')
    return
  last = messages[-1]
  content = getattr(last, 'content', '')
  print(f'Assistant: {content}')

def _print_interrupt(interrupt) -> None:
  question = interrupt.value['question']
  details = interrupt.value['details']
  if question:
    print(f'Interrupt: {question}')
  if details:
    print(details)

def main() -> None:
  repository = JsonRepository(file_name='test.json')
  Task.set_repository(repository)
  config = { "configurable": { "thread_id": "interactive-tests" } }
  messages = []
  interruption = False

  print('Interactive graph runner. Type /exit to quit.')

  while True:
    user_input = input('You: ').strip()
    if not user_input:
      continue
    if user_input.lower() == '/exit':
      break

    if interruption:
      result = graph.invoke(Command(resume=user_input), config=config, version='v2')
    else:
      messages.append(HumanMessage(content=user_input))
      state = { "messages": messages }
      result = graph.invoke(state, config=config, version='v2')

    if result.interrupts:
      _print_interrupt(result.interrupts[0])
      interruption = True
    else:
      messages = result.value['messages']
      _print_last_message(messages)
      interruption = False

    if len(messages) > 10:
      messages = messages[-10:]

if __name__ == '__main__':
  main()
