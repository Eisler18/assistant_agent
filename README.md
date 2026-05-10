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
- [LangSmith Tracing](docs/langsmith.md) - Trace setup and evidence for graph runs
- [Graph Architecture](docs/graph.md) - Node topology, tools, and routing logic

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
