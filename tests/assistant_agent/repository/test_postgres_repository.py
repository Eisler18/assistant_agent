
import os

import pytest
from task_scenarios import assert_get_and_not_found, assert_list_filters, create_task
from assistant_agent.models import Task
from assistant_agent.repository.postgres_repository import PostgresRepository
from assistant_agent.repository.schema import metadata

TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL')

pytestmark = pytest.mark.integration

requires_test_db = pytest.mark.skipif(
  not TEST_DATABASE_URL,
  reason='TEST_DATABASE_URL is not set; skipping Postgres repository integration tests'
)

# ------------------------------------------------------------------ #
# Fixtures                                                           #
# ------------------------------------------------------------------ #
@pytest.fixture(name='repo')
def fixture_repo(schema_url):
  repository = PostgresRepository(database_url=schema_url)
  metadata.create_all(repository.engine)
  return repository

@pytest.fixture(autouse=True)
def reset_task_repository():
  '''
  Task.repository is a shared ClassVar. Without resetting it, a test here
  leaves Task pointed at a repository backed by a schema that gets dropped
  once this module's tests finish, breaking any later test relying on
  Task.repository being None (or its own value).
  '''
  yield
  Task.set_repository(None)

# ------------------------------------------------------------------ #
# PostgresRepository                                                 #
# ------------------------------------------------------------------ #
@requires_test_db
class TestPostgresRepository:
  def test_save_and_get(self, repo):
    Task.set_repository(repo)
    task = create_task()

    assert_get_and_not_found(repo, task)

  def test_upsert_on_save(self, repo):
    Task.set_repository(repo)
    task = create_task(title='Original Title')

    task.update(title='Updated Title')

    retrieved = repo.get(str(task.id))
    assert len(repo.list()) == 1
    assert retrieved['title'] == 'Updated Title'

  def test_list(self, repo):
    Task.set_repository(repo)
    assert_list_filters(repo)

  def test_data_persistence_across_instances(self, schema_url):
    repo1 = PostgresRepository(database_url=schema_url)
    metadata.create_all(repo1.engine)
    Task.set_repository(repo1)
    task = create_task(title='Task 1')

    repo2 = PostgresRepository(database_url=schema_url)
    retrieved = repo2.get(str(task.id))
    assert retrieved['id'] == str(task.id)
