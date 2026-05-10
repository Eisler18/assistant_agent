# Graph Architecture

## Overview

The graph is a LangGraph `StateGraph` with explicit node routing. Nodes orchestrate
LLM decisions, while tools execute side effects such as repository calls or
calendar link generation. Tool execution is managed through `ToolNode`.

## Topology

```mermaid
flowchart TD
  START([START]) --> intent_classifier[intent_classifier]
  intent_classifier -->|task_crud| task_crud[task_crud]
  intent_classifier -->|briefing| briefing[briefing]
  intent_classifier -->|unknown| END([END])

  task_crud -->|tool_calls| task_tools[task_tools]
  task_tools --> task_crud
  task_crud -->|no tool_calls| END

  briefing -->|tool_calls| briefing_tools[briefing_tools]
  briefing_tools --> briefing
  briefing -->|no tool_calls| END
```

## Agent State

| Field | Type | Default | Owner | Notes |
| --- | --- | --- | --- | --- |
| `messages` | `list` (reducer: `add_messages`) | `[]` | All nodes | Full conversation history; reducer merges by message id. |
| `intent` | `Literal['task_crud', 'briefing', 'unknown']` | `unknown` | Intent classifier | Drives the routing decision after classification. |

## Tools

| Domain | Tool | Description |
| --- | --- | --- |
| Task CRUD | `create_task` | Create a new task in the repository. |
| Task CRUD | `get_task` | Retrieve a task by id. |
| Task CRUD | `list_tasks` | List tasks using structured filters. |
| Task CRUD | `update_task` | Update task fields (including rescheduling). |
| Task CRUD | `delete_task` | Soft-delete a task by id. |
| Filter builders | `parse_date` | Parse a natural language date into an ISO datetime. |
| Filter builders | `parse_date_range` | Parse a natural language date range into ISO bounds. |
| Filter builders | `build_overdue_filter` | Build a filter for overdue tasks. |
| Filter builders | `build_today_filter` | Build a filter for tasks planned for today. |
| Filter builders | `build_unscheduled_filter` | Build a filter for tasks with deadlines but no plan. |
| Briefing | `get_daily_briefing_data` | Summarize overdue, today, upcoming, and unscheduled tasks. |
| Calendar | `generate_calendar_link` | Generate a quick-add calendar link. |

## Routing Logic

- `intent_classifier` sets `state['intent']` based on the user prompt.
- `route_by_intent` sends the state to `task_crud`, `briefing`, or `END`.
- `should_continue` inspects the last message and routes to the tool node if
  tool calls are present, otherwise it ends the run.

## MemorySaver Checkpointing

The graph is compiled with `InMemorySaver` for short-lived session memory.
Callers must pass a thread id to retain state between turns:

```python
result = graph.invoke(state, config={"configurable": {"thread_id": "session-1"}})
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
scenarios. Each node invocation (intent classifier, tool loops, and terminal responses)
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
