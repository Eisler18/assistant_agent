import os
import time
from typing import Any
from langsmith import Client as _Client


def get_run_metrics(run_name: str, project_name: str = 'assistant_agent') -> dict[str, Any] | None:
  if not os.getenv('LANGCHAIN_TRACING_V2', '').lower() == 'true':
    return None

  if _Client is None:
    return None

  try:
    client = _Client()
    time.sleep(2)
    filter_str = f'eq(name, "{run_name}")'
    runs = list(
      client.list_runs(project_name=project_name, filter=filter_str)
    )
    if not runs:
      return None
    run = runs[0]

    latency_ms = None
    if getattr(run, 'start_time', None) and getattr(run, 'end_time', None):
      try:
        latency_ms = (run.end_time - run.start_time).total_seconds() * 1000
      except Exception: # pylint: disable=broad-except
        latency_ms = None

    return {
      'run_id': str(getattr(run, 'id', None)),
      'total_tokens': getattr(run, 'total_tokens', None),
      'prompt_tokens': getattr(run, 'prompt_tokens', None),
      'completion_tokens': getattr(run, 'completion_tokens', None),
      'latency_ms': latency_ms,
    }
  except Exception: # pylint: disable=broad-except
    return None
