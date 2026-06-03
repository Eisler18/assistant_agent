# assistant_agent

Small project for master's degree thesis at Universidad Politecnica de Madrid

## Overview

A time management assistant agent that helps users organize and manage their tasks efficiently.

## Project Structure

```
assistant_agent/
├── src/
│   └── assistant_agent/
│       ├── graph/            # LangGraph definition and related logic
│       ├── models/           # Data models (Task, TaskStatus)
│       ├── repository/       # Data persistence layer
│       |── utils/            # Utility functions
|       └── config.py         # Configuration (LLM, graph, etc.) 
├── tests/                    # Test suite
├── docs/                     # Project documentation
└── data/                     # Data files
```

## Documentation

- [Models](docs/models.md) - Core data models including Task entity and lifecycle management
- [Repository](docs/repository.md) - Data persistence approach
- [Workflow Architecture](docs/graph.md) - Node topology, tools, and routing logic
- [ReAct Agent Architecture](docs/react_agent.md) - Alternative agent design using ReAct pattern
- [Evaluation framework](docs/evaluation.md) - Scenario runner, assertions, and reporting

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Installation

```bash
uv sync
```

### Running Tests

```bash
uv run pytest
uv run pylint tests/
uv run pylint src/
```
