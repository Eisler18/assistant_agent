
from .base import BaseRepository
from .json_repository import JsonRepository
from .postgres_repository import PostgresRepository


def build_repository(database_url: str | None) -> BaseRepository:
  '''
  Mirrors assistant_agent.graph.checkpointer.build_checkpointer's
  ENVIRONMENT-driven fallback: Postgres when a database URL is configured,
  otherwise JsonRepository so the app still runs without Docker.
  '''
  if not database_url:
    return JsonRepository(file_name='tasks.json')

  return PostgresRepository(database_url=database_url)
