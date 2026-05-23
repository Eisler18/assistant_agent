# Graph Architecture

## Overview

The graph is a LangGraph `StateGraph` with explicit node routing per intent. Nodes orchestrate
LLM decisions, while tools execute side effects such as repository calls. Tool execution is
managed through `ToolNode`.

## Topology

```mermaid
flowchart TD
  START([START]) --> session_initialiser
  session_initialiser --Briefing--> END
  session_initialiser --Briefing already shown--> intent_classifier
  intent_classifier --Create --> task_create
  intent_classifier --Update --> task_update
  intent_classifier --Read --> task_read
  intent_classifier --Unknown --> END

  task_read --> END
  task_create --> END
  task_update --> END
  task_interrupt --> END

  task_read --Tools--> task_read_tools --> task_read
  task_create --Other tools --> task_create_tools --> task_create
  task_update --Other tools --> task_update_tools --> task_update

  task_update -->|write tool| task_interrupt
  task_create -->|write tool| task_interrupt
  task_interrupt -->|confirm| task_create_tools
  task_interrupt -->|confirm| task_update_tools
  task_interrupt -->|cancel| END

  intent_classifier[intent_classifier]
  task_read[task_read]
  task_create[task_create]
  task_update[task_update]
  task_read_tools[task_read_tools]
  task_create_tools[task_create_tools]
  task_update_tools[task_update_tools]
  task_interrupt[task_interrupt]
  session_initialiser[session_initialiser]
  END([END])
```

## Agent State

| Field | Type | Default | Owner | Notes |
| --- | --- | --- | --- | --- |
| `messages` | `list` (reducer: `add_messages`) | `[]` | All nodes | Full conversation history; reducer merges by message id. |
| `intent` | `Literal['task_create', 'task_read', 'task_update', 'unknown']` | `unknown` | Intent classifier | Drives the routing decision after classification. |
| `confirmation` | `bool | None` | `None` | Interrupt node | Set when the user confirms a write action. |
| `cancelled` | `bool | None` | `None` | Interrupt node | Set when the user cancels a write action. |
| `briefing_shown` | `bool` | `False` | Session initialiser | Prevents re-emitting the daily briefing in the same session. |

## Tools

| Domain | Tool | Description |
| --- | --- | --- |
| Task CRUD | `create_task` | Create a new task in the repository. |
| Task CRUD | `get_task` | Retrieve a task by id. |
| Task CRUD | `list_tasks` | List tasks using structured filters. |
| Task CRUD | `update_task` | Update task fields (including rescheduling). |
| Task CRUD | `delete_task` | Soft-delete a task by id (used via the update toolset). |
| Filter builders | `parse_date_range` | Parse a natural language date range into ISO bounds. |
| Filter builders | `build_overdue_filter` | Build a filter for overdue tasks. |
| Filter builders | `build_today_filter` | Build a filter for tasks planned for today. |
| Filter builders | `build_unscheduled_filter` | Build a filter for tasks with deadlines but no plan. |
| Briefing | `get_daily_briefing_data` | Return `{overdue,today,upcoming,unscheduled}` arrays of task dicts. |

## Routing Logic

- `session_initialiser` emits a briefing once per session and ends the graph when no user
  message is present.
- `intent_classifier` sets `state['intent']` based on the user prompt.
- `route_by_intent` sends the state to `task_read`, `task_create`, `task_update`, or `END`.
- `should_continue` inspects the last message and routes to the tool node if tool calls are
  present; write tools (`create_task`, `update_task`, `delete_task`) route to the interrupt.
- `should_save_task` decides whether to proceed with the write tools after confirmation.

## MemorySaver Checkpointing

The graph is compiled with `InMemorySaver` for short-lived session memory.
Callers must pass a thread id to retain state between turns:

```python
result = graph.invoke(state, config={"configurable": {"thread_id": "session-1"}}, version="v2")
```

This allows consecutive turns to reuse the stored message history. The
in-memory checkpointer is suitable for development and thesis experiments; a
persistent saver (for example, SQLite) can replace it later.

## Design Rationale

An explicit node topology was chosen over a single ReAct agent because it:

- Separates intent classification from execution.
- Makes tool usage and routing decisions traceable in LangSmith.
- Aligns with the thesis focus on explicit orchestration and evaluation.

## Monitoring: LangSmith

This project uses LangSmith to capture execution traces for LangGraph runs in non-test
scenarios. Each node invocation (intent classifier, tool loops, and interrupt responses)
appears as a separate span, which makes routing decisions and tool usage easy to inspect
and cite in the thesis.

### Setup

1. Create a LangSmith account and an API key.
2. Add the following to your environment (or .env file):

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your-langsmith-key-here
LANGCHAIN_PROJECT=assistant_agent
```

### How It Works

LangSmith is enabled through the `LANGCHAIN_TRACING_V2` environment variable. When it is
`true`, LangChain automatically records traces for every graph run, including:

- The input prompt and messages flowing through the graph
- Node-level routing decisions (intent classifier, task CRUD, briefing)
- Tool call inputs and outputs

Tests disable tracing to keep the suite isolated and deterministic. Traces are only
recorded for real runs launched from scripts or a REPL.

Trace example: https://eu.smith.langchain.com/public/b80c96ad-810a-432a-a5fc-67193223ab40/r

## Session Initialiser

The `session_initialiser` node runs at session start, emits a single briefing message, and
sets `briefing_shown=True` in state. If no `HumanMessage` exists in state, the graph ends
after the briefing; the next user message triggers intent classification in a new invocation.
When a user message is present, the graph proceeds to `intent_classifier` immediately after
the briefing.
