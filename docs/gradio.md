# Gradio Interface Implementation

## Overview

The `src/app` package is the presentation layer of the assistant. It provides a
chat interface with Gradio, forwards user events to LangGraph, and renders graph
responses back to the UI

The layer is intentionally thin:

- UI concerns stay in `src/app`
- domain logic stays in `src/assistant_agent`
- persistence remains in the repository layer

For graph internals, see `docs/graph.md` and `docs/react_agent.md`

## Session State Contract

| Field | Type | Default | Purpose |
| --- | --- | --- | --- |
| `thread_id` | `str` | `None` | `None` | Checkpoint key passed to graph `configurable.thread_id` |
| `is_interrupted` | `bool` | `False` | Indicates that next user action should call `resume_turn` |

## Turn Lifecycle

1. `demo.load` calls `on_session_start`
2. The app creates a `thread_id` and requests a daily briefing turn
3. User sends input via button click or Enter
4. `handle_user_message` updates chat history
5. `handle_ai_response` routes execution:
   - normal path: `invoke_turn(...)`
   - interrupted path: `resume_turn(...)`
6. `TurnResult.messages` is mapped to Gradio format
7. If interruption exists, confirmation controls are shown
8. User clicks `Confirm` or `Cancel`, both routed through `resume_turn(...)`

## Interrupt Confirmation Behavior

Write operations are mediated through a human confirmation step:

- graph emits interrupt payload
- UI displays a confirmation label with optional details
- user responds explicitly (`yes`/`no`)
- graph continues in the same thread context

This preserves safety for state-changing operations while keeping the interaction
inside one chat session

## Configuration

### Graph selection

- default behavior: [Workflow graph](graph.md)
- `AGENT_GRAPH=react`: [ReAct agent](react_agent.md)

### Repository file

The UI adapter configures task persistence with `tasks.json` through
`JsonRepository(file_name='tasks.json')`

More details on the repository pattern in [`docs/repository.md`](repository.md).

## Run Commands

Install dependencies and start the app:

```bash
uv sync
uv run assistant-agent
```

Run with ReAct graph:

```bash
AGENT_GRAPH=react uv run assistant-agent
```

## Design Rationale

- Keeps UI orchestration separate from graph and repository internals
- Makes interruption handling explicit in the presentation layer
- Supports both graph strategies behind a stable UI contract
