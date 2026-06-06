# assistant_agent

Small project for master's degree thesis at Universidad Politecnica de Madrid

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
│   │   ├── repository/       # Repository abstractions and JSON implementation
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

The app will be available at http://localhost:7860 and will persist task data in `./data`

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
