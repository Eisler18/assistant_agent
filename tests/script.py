from langchain_core.messages import HumanMessage
from langgraph.types import Command

from assistant_agent.graph.graph import graph
from assistant_agent.graph.state import AgentState
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
  repository = JsonRepository(file_name='tasks.json')
  Task.set_repository(repository)
  config = { "configurable": { "thread_id": "initializer-tests" } }
  state = AgentState(messages=[HumanMessage(content='Generate a daily briefing of my tasks')])
  interruption = False

  print('\nInteractive graph runner. Type /exit to quit.\n')

  result = graph.invoke(state, config=config, version='v2')
  state = result.value if result.value else state
  initial_message = state['messages'][-1] if state['messages'] else None
  if initial_message:
    print(f'{initial_message.content}\n')

  while True:
    user_input = input('You: ').strip()
    if not user_input:
      continue
    if user_input.lower() == '/exit':
      break

    if interruption:
      result = graph.invoke(Command(resume=user_input), config=config, version='v2')
    else:
      state['messages'].append(HumanMessage(content=user_input))
      result = graph.invoke(state, config=config, version='v2')

    state = result.value if result.value else state

    if result.interrupts:
      _print_interrupt(result.interrupts[0])
      interruption = True
    else:
      _print_last_message(state['messages'])
      interruption = False

    if len(state['messages']) > 10:
      state['messages'] = state['messages'][-10:]

if __name__ == '__main__':
  main()
