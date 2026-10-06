
from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import Pool


def build_engine(database_url: str, poolclass: type[Pool] | None = None) -> Engine:
  '''
  psycopg (v3) is the driver already used by the LangGraph checkpointer, but
  SQLAlchemy's postgresql:// scheme defaults to psycopg2. Force psycopg3
  instead of adding psycopg2 as a second Postgres driver dependency.
  '''
  url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
  kwargs = {} if poolclass is None else {'poolclass': poolclass}
  return create_engine(url, **kwargs)
