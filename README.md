# Intelligent Assistant Agent

## Overview

A time management assistant agent that helps users organize and manage their tasks efficiently.

## Project Structure

```
assistant_agent/
├── data/                     # JSON task storage
├── docs/                     # Project documentation
├── src/
│   ├── app/                  # Gradio interface layer
│   │   ├── app.py            # UI layout and event handlers
│   │   ├── graph_runner.py   # Invoke/resume graph turns
│   │   └── formatting.py     # LangChain-to-Gradio message mapping
│   ├── assistant_agent/      # Core assistant domain and workflows
│   │   ├── graph/            # Workflow graph, nodes, tools, state
│   │   ├── models/           # Domain entities (Task)
│   │   ├── repository/       # Repository abstractions, JSON and Postgres implementations
│   │   ├── utils/            # Shared utilities (date parsing)
│   │   └── config.py         # Runtime and model configuration
│   └── evaluation/           # Evaluation pipeline
│       ├── runner.py         # Evaluation CLI entrypoint
│       ├── assertions.py     # Deterministic and statistical checks
│       ├── scenarios/        # YAML scenario suites
│       └── report.py         # JSON report generation
├── tests/                    # Test suite
└── results/                  # Evaluation output artifacts
```

## Documentation

- [Models](docs/models.md) - Core data models including Task entity and lifecycle management
- [Repository](docs/repository.md) - Data persistence approach
- [Workflow Architecture](docs/graph.md) - Node topology, tools, and routing logic
- [ReAct Agent Architecture](docs/react_agent.md) - Alternative agent design using ReAct pattern
- [Gradio Interface](docs/gradio.md) - UI handlers, turn lifecycle, and interrupt flow in `src/app`
- [Evaluation framework](docs/evaluation.md) - Scenario runner, assertions, and reporting

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Installation

```bash
uv sync
```

### Running the Gradio App

Start the default app:

```bash
uv run assistant-agent
```

Run with the ReAct graph:

```bash
AGENT_GRAPH=react uv run assistant-agent
```

### Running with Docker Compose

Start the app in detached mode:

```bash
docker compose up -d --build
```

The app will be available at http://localhost:7860.

`docker-compose.yml` also starts a `postgres` service the app depends on, used to persist
both graph checkpoints (conversation state, including pending interrupts) and tasks across
restarts — see [Checkpointing](docs/graph.md#checkpointing) and
[Repository](docs/repository.md) for details. The `assistant-agent` container runs any
pending Alembic migrations automatically on startup (`docker-entrypoint.sh`) before the app
starts, so `docker compose up` self-provisions the `tasks` table schema. If `DATABASE_URL`
is left unset, the app falls back to `./data` for task storage instead (see
[Repository](docs/repository.md)).

### Database Migrations

Schema changes to Postgres-backed models (currently just `tasks`) go through
[Alembic](https://alembic.sqlalchemy.org/), targeting whichever `*_DATABASE_URL`
`ENVIRONMENT` resolves to (see [Checkpointing](docs/graph.md#checkpointing)):

```bash
# Apply pending migrations (e.g. after pulling changes, or against a fresh dev DB)
uv run alembic upgrade head

# After changing src/assistant_agent/repository/schema.py, generate a migration
# and review the generated file in migrations/versions/ before committing it
uv run alembic revision --autogenerate -m "describe the change"
```

See [Repository](docs/repository.md#schema-and-migrations) for why Alembic is scoped to
avoid the tables the LangGraph checkpointer manages on its own.

Additionally, deployment workflow can be tested locally using act:

```bash
act -W .github/workflows/release-smoke-test.yml -j smoke-test-api -s LLM_MODEL_NAME="model-name" -s LLM_API_KEY="api-key" -s LLM_API_URL="api-url"
```

Or adding the secrets to the predefined act event:

```bash
act -W .github/workflows/release-smoke-test.yml -j smoke-test-api -e act/release-smoke-test.json
```

### Running Tests

```bash
uv run pytest
uv run pylint tests/
uv run pylint src/
```

The default `pytest` run is DB-free (it doesn't require Postgres). A separate
set of integration tests exercises the real Postgres checkpointer and is
skipped automatically unless `TEST_DATABASE_URL` is set.

These tests expect their own `assistant_agent_test` database, kept separate
from development data. It isn't created automatically — create it once
after starting `postgres` (`createdb` errors harmlessly if it already
exists; only needed again if the `postgres-data` volume is recreated):

```bash
docker compose up -d postgres
docker compose exec postgres createdb -U assistant_agent assistant_agent_test
```

Then run the integration tests against it:

```bash
TEST_DATABASE_URL=postgresql://assistant_agent:assistant_agent@localhost:5432/assistant_agent_test \
  uv run pytest tests/assistant_agent/graph/test_checkpointer.py
```

## Evaluation

Evaluation is implemented in `src/evaluation` and documented in
[`docs/evaluation.md`](docs/evaluation.md).

### What is evaluated

- Scenario-based conversations (create, read, update, routing, briefing)
- Tool usage and control-flow behavior (including interrupts)
- Repository state outcomes after each run
- Optional tracing metrics when LangSmith is enabled

### Scenario files

Scenarios are stored in `src/evaluation/scenarios/` and define:

- User message sequences
- Optional initial repository state
- Assertions over messages, tools, and repository state

### Run evaluation

Validate a scenario schema without calling the model:

```bash
uv run -m src.evaluation.runner --scenarios create_tests.yaml --dry-run
```

Run a single scenario:

```bash
uv run -m src.evaluation.runner \
	--scenarios create_tests.yaml \
	--scenario create_task_title_only \
	--runs 1 \
	--output results/smoke.json
```

Run a full evaluation suite:

```bash
uv run -m src.evaluation.runner --scenarios create_tests.yaml --runs 5 --output results/create.json
```

### Evaluation outputs

- JSON reports written to `results/`
- Optional trace/token/latency data when tracing is enabled
- Per-run assertion pass/fail summaries
