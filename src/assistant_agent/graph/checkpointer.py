
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def build_checkpointer(database_url: str | None) -> BaseCheckpointSaver:
  if not database_url:
    return InMemorySaver()

  pool = ConnectionPool(
    conninfo=database_url,
    max_size=10,
    kwargs={ 'autocommit': True, 'row_factory': dict_row },
  )
  checkpointer = PostgresSaver(pool)
  checkpointer.setup()
  return checkpointer
