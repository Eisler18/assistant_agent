
from sqlalchemy import (
  Column,
  DateTime,
  Integer,
  MetaData,
  String,
  Table,
)

metadata = MetaData()

tasks = Table(
  'tasks', metadata,
  Column('id', String, primary_key=True),
  Column('title', String, nullable=False),
  Column('description', String, nullable=True),
  Column('deadline', DateTime(timezone=True), nullable=True),
  Column('planned_at', DateTime(timezone=True), nullable=True),
  Column('estimated_minutes', Integer, nullable=True),
  Column('status', String, nullable=False),
  Column('created_at', DateTime(timezone=True), nullable=False),
  Column('updated_at', DateTime(timezone=True), nullable=False),
  Column('completed_at', DateTime(timezone=True), nullable=True),
)
