#!/bin/sh
set -e

# DATABASE_URL drives both the LangGraph checkpointer and the task
# repository (see assistant_agent.config.Config, docs/graph.md's
# "Checkpointing" section). Only run migrations when it's actually set --
# an unset DATABASE_URL means the in-memory checkpointer/JsonRepository
# fallback is intended, and there's nothing to migrate.
if [ -n "$DATABASE_URL" ]; then
  echo "Running database migrations..."
  uv run alembic upgrade head
fi

exec uv run assistant-agent
