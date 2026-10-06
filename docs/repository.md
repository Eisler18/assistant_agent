# Repository Pattern

This document describes the repository pattern used for data persistence in the Assistant Agent.

## Overview

The repository pattern provides a layer of abstraction between the domain models and the data access layer. This allows for:
- Flexible persistence strategies
- Easy testing with mock repositories
- Decoupling models from storage implementation
- Consistent data access patterns

## Architecture

```mermaid
---
title: Repository Architecture
---
graph TB
    A[Task Model] -->|uses| B[Repository Interface]
    B -->|implemented by| C[JsonRepository]
    B -->|implemented by| G[PostgresRepository]
    B -->|can be| D[MockRepository]
    C -->|persists to| E[JSON File]
    G -->|persists to| H[Postgres: tasks table]
    D -->|for| F[Testing]

    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style G fill:#f3e5f5
    style E fill:#e8f5e9
    style H fill:#e8f5e9
```

## Which implementation is used

`build_repository` (`assistant_agent.repository.factory`) picks the implementation the same
way `assistant_agent.graph.checkpointer.build_checkpointer` picks a checkpointer: driven by
`Config.database_url`, which is itself `ENVIRONMENT`-driven (see `docs/graph.md`'s
"Checkpointing" section).

- When a database URL is configured, `PostgresRepository` is used — the same Postgres
  instance backs both LangGraph checkpoints and tasks ("shared database, separate tables").
- When it's unset, `JsonRepository` is used as a fallback so the app still runs without
  Docker — mirroring the in-memory checkpointer fallback.

`app/graph_runner.py`'s `_setup_repository()` is the real app's call site. The evaluation
harness (`src/evaluation/seeder.py`, `runner.py`) deliberately always uses `JsonRepository`
directly instead, for cheap, disposable, per-scenario fixtures — it doesn't go through
`build_repository`.

## BaseRepository

The `BaseRepository` is an abstract interface defining the contract for all repository implementations.

### Interface

```python
class BaseRepository(ABC):
  @abstractmethod
  def save(self, task: Dict[str, Any]) -> None:
    """Persist a task to storage"""
    pass

  @abstractmethod
  def get(self, task_id: str) -> Dict[str, Any]:
    """Retrieve a task by ID"""
    pass

  @abstractmethod
  def list(self, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Retrieve tasks with optional filtering"""
    pass
```

## JsonRepository

The `JsonRepository` is the primary implementation that persists tasks to JSON files.

### Initialization

```python
from assistant_agent.repository import JsonRepository

# Default: uses data/dump.json in project root
repo = JsonRepository()

# Custom root path
repo = JsonRepository(root_path="./custom_data")

# Custom file name
repo = JsonRepository(file_name="tasks.json")
```

### Features

- **Automatic directory creation**: Creates target directory if it doesn't exist
- **File initialization**: Creates empty JSON object if file doesn't exist
- **Flexible configuration**: Supports custom root paths and file names
- **Dictionary-based interface**: Works with dictionaries for compatibility (use `Task.to_dict()` and `Task.from_dict()` for conversion)

### Methods

#### `save(task: Dict[str, Any])`

Persists a task to the JSON file. Creates or overwrites the task using its `id` as the key.

```python
task_dict = {
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Write Report",
  "description": "Q1 Report",
  "estimated_minutes": 120,
  "status": "pending",
  "created_at": "2026-04-01T10:30:00+00:00",
  "updated_at": "2026-04-01T10:30:00+00:00",
  "completed_at": None,
  "deadline": None,
  "planned_at": None
}

repo.save(task_dict)
```

#### `get(task_id: str)`

Retrieves a task by its ID. Raises `KeyError` if not found.

```python
task_dict = repo.get("123e4567-e89b-12d3-a456-426614174000")
```

#### `list(query: Dict[str, Any] = None)`

Retrieves all tasks, optionally filtered by query criteria.

```python
# Get all tasks
all_tasks = repo.list()

# Filter by status
pending = repo.list({"status": "pending"})

# Filter by multiple criteria
completed_by_user = repo.list({"status": "completed", "title": "Write Report"})
```

## PostgresRepository

The `PostgresRepository` persists tasks to a `tasks` table via SQLAlchemy Core (`Table`,
`select`, `insert`) — no declarative ORM models, matching the plain, explicit style used
elsewhere in the repo (`JsonRepository`, `graph/checkpointer.py`'s raw `psycopg`).

### Initialization

```python
from assistant_agent.repository import PostgresRepository

# From a connection URL
repo = PostgresRepository(database_url="postgresql://user:pass@localhost:5432/assistant_agent")

# Or from an existing SQLAlchemy Engine (e.g. for a pre-configured connection pool)
repo = PostgresRepository(engine=my_engine)
```

`database_url` accepts the plain `postgresql://` scheme (the same string
`Config.database_url` resolves and the checkpointer's `psycopg.connect` uses) —
`PostgresRepository` rewrites it to `postgresql+psycopg://` internally
(`assistant_agent.repository.engine.build_engine`) so SQLAlchemy uses the psycopg3 driver
already installed for the checkpointer, instead of adding `psycopg2` as a second Postgres
driver dependency.

### Schema and migrations

The `tasks` table is defined once, as SQLAlchemy metadata, in
`assistant_agent/repository/schema.py` — imported by both `PostgresRepository` and Alembic's
`migrations/env.py` (for autogenerate). Schema changes go through Alembic:

```bash
# After changing schema.py, generate a migration:
uv run alembic revision --autogenerate -m "describe the change"

# Review the generated file in migrations/versions/, then apply it:
uv run alembic upgrade head
```

**Alembic and the LangGraph checkpointer manage separate tables in the same database.**
`PostgresSaver.setup()` (see `graph/checkpointer.py`) owns its own tables (`checkpoints`,
`checkpoint_blobs`, `checkpoint_writes`, `checkpoint_migrations`) independently of Alembic.
`migrations/env.py` restricts Alembic's autogenerate/compare to tables declared in
`schema.py`'s metadata (via an `include_name` filter) specifically so it never proposes
dropping the checkpointer's tables as "unknown" — without that filter, autogenerate detects
them as unmanaged and generates `DROP TABLE` migrations for them.

In production, migrations run automatically on container startup (`docker-entrypoint.sh`
runs `alembic upgrade head` before the app starts, when `DATABASE_URL` is set).

### Methods

Same `save`/`get`/`list` contract as `BaseRepository` — behaves identically to
`JsonRepository` from the `Task` model's perspective (same dict shape in and out, same
`KeyError` on a missing `get`, same upsert-by-`id` semantics on `save`, same `TaskFilter`
query support). Query filtering is implemented as SQL `WHERE` clauses instead of Python-side
filtering.

## Dependency Injection

The repository is injected into models . This provides:
- **Testability**: Easy to mock for unit tests
- **Flexibility**: Can switch implementations at runtime
- **Isolation**: No shared state between tests

### Setting the Repository

```python
from assistant_agent.models.task import Task
from assistant_agent.repository import JsonRepository

# In your application initialization
def setup():
    repo = JsonRepository(file_name="tasks.json")
    Task.set_repository(repo)

# Call once on startup
setup()
```

### Working Without Repository

Models work without a repository (useful for testing without persistence):

```python
from assistant_agent.models.task import Task

# Ensure no repository is set
Task.set_repository(None)

# Create and update tasks without persistence
task = Task.create(title="Task")
updated = task.update(title="Updated")
```

## File Format

Tasks are stored as a JSON object with task IDs as keys:

```json
{
  "123e4567-e89b-12d3-a456-426614174000": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Write Report",
    "description": "Q1 Report",
    "estimated_minutes": 120,
    "status": "pending",
    "created_at": "2026-04-01T10:30:00+00:00",
    "updated_at": "2026-04-01T10:30:00+00:00",
    "completed_at": null,
    "deadline": null,
    "planned_at": null
  },
  "987f6543-a21c-45d6-e789-123456789abc": {
    "id": "987f6543-a21c-45d6-e789-123456789abc",
    "title": "Code Review",
    "description": null,
    "estimated_minutes": 30,
    "status": "completed",
    "created_at": "2026-03-30T14:15:00+00:00",
    "updated_at": "2026-04-01T09:00:00+00:00",
    "completed_at": "2026-04-01T09:30:00+00:00",
    "deadline": null,
    "planned_at": null
  }
}
```
