
import os
import uuid

import psycopg
import pytest

TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL')


@pytest.fixture(name='schema_url')
def fixture_schema_url():
  '''
  A throwaway Postgres schema for one test, isolating it from other tests
  and from any pre-existing data in TEST_DATABASE_URL. Shared by any
  integration test that needs its own Postgres-backed schema (graph
  checkpointer, task repository).
  '''
  schema = f'test_schema_{uuid.uuid4().hex}'

  with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as conn:
    conn.execute(f'CREATE SCHEMA "{schema}"')

  yield f'{TEST_DATABASE_URL}?options=-csearch_path%3D{schema}'

  with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as conn:
    conn.execute(f'DROP SCHEMA "{schema}" CASCADE')
