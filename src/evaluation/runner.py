from dataclasses import dataclass
from pathlib import Path
import argparse
import tempfile
from typing import Any
from uuid import uuid4
import os

import yaml
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from assistant_agent.graph.graph import graph
from assistant_agent.models.task import Task

from .assertions import (
  AssertionResult,
  assert_calendar_link_in_response,
  assert_interrupt_fired,
  assert_repository_count_delta,
  assert_repository_task_absent,
  assert_repository_task_exists,
  assert_task_field_date_within,
  assert_task_field_equals,
  assert_task_not_saved_before_interrupt,
  assert_tool_call_order,
  assert_tools_called_include,
  assert_tools_not_called
)
from .seeder import ensure_seed, setup_repository
from .trace import extract_tool_calls
from .langsmith_client import get_run_metrics
from .report import aggregate_results, write_json_report, print_terminal_summary


@dataclass(frozen=True)
class ScenarioTurn:
  user: str | None
  interrupt: str | None


@dataclass(frozen=True)
class Scenario:
  id: str
  description: str
  seed: Path
  repetitions: int
  turns: list[ScenarioTurn]
  assertions: list[dict[str, Any]]
  initial_state: dict[str, Any]


@dataclass(frozen=True)
class ScenarioResult:
  scenario_id: str
  run_index: int
  assertions: list[AssertionResult]
  error: str | None
  langsmith_data: dict[str, Any] | None


def _require(cfg: dict[str, Any], field: str, path: Path) -> Any:
  if field not in cfg:
    raise ValueError(f"{path}: missing required field '{field}'")
  return cfg[field]


def load_scenario(scenario_dict: dict[str, Any], path: Path) -> Scenario:

  scenario_id = _require(scenario_dict, 'id', path)
  description = _require(scenario_dict, 'description', path)
  seed_value = _require(scenario_dict, 'seed', path)
  turns_value = _require(scenario_dict, 'turns', path)
  assertions_value = _require(scenario_dict, 'assertions', path)

  if not isinstance(turns_value, list) or not turns_value:
    raise ValueError(f'{path}: turns must be a non-empty list')
  if not isinstance(assertions_value, list):
    raise ValueError(f'{path}: assertions must be a list')

  turns: list[ScenarioTurn] = []
  for idx, turn in enumerate(turns_value):
    if not isinstance(turn, dict):
      raise ValueError(f'{path}: turn {idx} must be a mapping')
    user = turn.get('user')
    interrupt = turn.get('interrupt')
    if user is None and interrupt is None:
      raise ValueError(f'{path}: turn {idx} must include user or interrupt')
    turns.append(ScenarioTurn(user=user, interrupt=interrupt))

  repetitions = int(scenario_dict.get('repetitions', 5))
  initial_state = scenario_dict.get('initial_state') or {}
  if not isinstance(initial_state, dict):
    raise ValueError(f'{path}: initial_state must be a mapping')

  seed_path = (path.parent / seed_value).resolve()

  return Scenario(
    id=scenario_id,
    description=description,
    seed=seed_path,
    repetitions=repetitions,
    turns=turns,
    assertions=assertions_value,
    initial_state=initial_state
  )


def _get_task_title(cfg: dict[str, Any], path: Path) -> str:
  task_title = cfg.get('title') or cfg.get('task_title')
  if not task_title:
    raise ValueError(f"{path}: assertion missing task title")
  return task_title


def dispatch_assertion(
  assertion_cfg: dict[str, Any],
  state: dict[str, Any],
  repo,
  trace: list[str],
  pre_interrupt_count: int | None,
  initial_count: int | None,
  result,
  scenario_path: Path
) -> AssertionResult:
  # pylint: disable=too-many-arguments,too-many-positional-arguments
  # pylint: disable=too-many-return-statements,too-many-branches,too-many-locals
  assertion_type = assertion_cfg.get('type')
  if not assertion_type:
    raise ValueError(f"{scenario_path}: assertion missing 'type'")

  if assertion_type == 'repository_task_exists':
    field = _require(assertion_cfg, 'field', scenario_path)
    value = _require(assertion_cfg, 'value', scenario_path)
    return assert_repository_task_exists(repo, field, value)

  if assertion_type == 'repository_task_absent':
    field = _require(assertion_cfg, 'field', scenario_path)
    value = _require(assertion_cfg, 'value', scenario_path)
    return assert_repository_task_absent(repo, field, value)

  if assertion_type == 'repository_count_delta':
    delta = _require(assertion_cfg, 'delta', scenario_path)
    return assert_repository_count_delta(repo, initial_count, int(delta))

  if assertion_type == 'task_field_equals':
    task_title = _get_task_title(assertion_cfg, scenario_path)
    field = _require(assertion_cfg, 'field', scenario_path)
    value = _require(assertion_cfg, 'value', scenario_path)
    return assert_task_field_equals(repo, task_title, field, value)

  if assertion_type == 'task_field_date_within':
    task_title = _get_task_title(assertion_cfg, scenario_path)
    field = _require(assertion_cfg, 'field', scenario_path)
    expression = _require(assertion_cfg, 'expression', scenario_path)
    tolerance = _require(assertion_cfg, 'tolerance_hours', scenario_path)
    return assert_task_field_date_within(repo, task_title, field, expression, tolerance)

  if assertion_type == 'tools_called_include':
    tools = _require(assertion_cfg, 'tools', scenario_path)
    return assert_tools_called_include(trace, tools)

  if assertion_type == 'tools_not_called':
    tools = _require(assertion_cfg, 'tools', scenario_path)
    return assert_tools_not_called(trace, tools)

  if assertion_type == 'tool_call_order':
    before = _require(assertion_cfg, 'before', scenario_path)
    after = _require(assertion_cfg, 'after', scenario_path)
    return assert_tool_call_order(trace, before, after)

  if assertion_type == 'interrupt_fired':
    return assert_interrupt_fired(result)

  if assertion_type == 'task_not_saved_before_interrupt':
    return assert_task_not_saved_before_interrupt(pre_interrupt_count, initial_count)

  if assertion_type == 'calendar_link_in_response':
    messages = state.get('messages', [])
    return assert_calendar_link_in_response(messages)

  raise ValueError(f'{scenario_path}: unknown assertion type {assertion_type!r}')


def run_scenario_once(scenario: Scenario, tmp_dir: Path, run_idx: int) -> ScenarioResult:
  # pylint: disable=too-many-locals,broad-exception-caught
  ensure_seed(scenario.seed)
  repo = setup_repository(scenario.seed, tmp_dir)
  Task.set_repository(repo)
  initial_count = len(repo.list())
  pre_interrupt_count = None
  thread_id = f'{scenario.id}-{run_idx}-{uuid4()}'
  run_name = f"eval-{scenario.id}-{run_idx}-{uuid4().hex[:8]}"
  config = {"configurable": {"thread_id": thread_id}, "run_name": run_name}

  try:
    if not scenario.turns or scenario.turns[0].user is None:
      raise ValueError(f'{scenario.id}: first turn must include a user message')

    initial_state = {
      **scenario.initial_state,
      'messages': [HumanMessage(content=scenario.turns[0].user)]
    }
    result = graph.invoke(initial_state, config=config, version='v2')

    for turn in scenario.turns[1:]:
      if turn.interrupt is not None and result.interrupts:
        pre_interrupt_count = len(repo.list())
        result = graph.invoke(Command(resume=turn.interrupt), config=config, version='v2')
      elif turn.user:
        result = graph.invoke(
          {"messages": [HumanMessage(content=turn.user)]},
          config=config,
          version='v2'
        )

    final_state = result.value or {}
    messages = final_state.get('messages', [])
    trace = extract_tool_calls(messages)
    assertion_results = [
      dispatch_assertion(
        assertion_cfg,
        final_state,
        repo,
        trace,
        pre_interrupt_count,
        initial_count,
        result,
        scenario.seed
      )
      for assertion_cfg in scenario.assertions
    ]
    langsmith_data = get_run_metrics(run_name)
    return ScenarioResult(
      scenario_id=scenario.id,
      run_index=run_idx,
      assertions=assertion_results,
      error=None,
      langsmith_data=langsmith_data
    )
  except Exception as exc:
    langsmith_data = get_run_metrics(run_name)
    return ScenarioResult(
      scenario_id=scenario.id,
      run_index=run_idx,
      assertions=[],
      error=str(exc),
      langsmith_data=langsmith_data
    )
  finally:
    Task.set_repository(None)


def run_scenario(scenario: Scenario, runs: int) -> list[ScenarioResult]:
  results: list[ScenarioResult] = []
  for run_idx in range(runs):
    print(f'[{scenario.id}] run {run_idx + 1}/{runs}')
    with tempfile.TemporaryDirectory() as tmp_dir:
      result = run_scenario_once(scenario, Path(tmp_dir), run_idx)
      results.append(result)
  return results


def _load_scenarios(file_path: Path) -> list[Scenario]:
  with open(file_path, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)
  return [load_scenario(scenario_dict, file_path) for scenario_dict in data.get('scenarios', [])]


def main() -> int:
  parser = argparse.ArgumentParser(description='Evaluation scenario runner')
  parser.add_argument('--scenarios', type=str, required=True)
  parser.add_argument('--scenario', type=str, default=None)
  parser.add_argument('--runs', type=int, default=5)
  parser.add_argument('--output', type=Path, default=Path('results/report.json'))
  parser.add_argument('--dry-run', action='store_true')
  args = parser.parse_args()

  scenarios_path = Path.cwd() / 'src' / 'evaluation' / 'scenarios' / args.scenarios
  scenarios = _load_scenarios(scenarios_path)
  if args.scenario:
    scenarios = [scenario for scenario in scenarios if scenario.id == args.scenario]
    if not scenarios:
      raise ValueError(f'No scenario found with id {args.scenario!r}')

  if args.dry_run:
    print(f'Loaded {len(scenarios)} scenarios:')
    for scenario in scenarios:
      print(f"- {scenario.id}: {scenario.description}")
    return 0

  all_aggregated: list[dict] = []
  for scenario in scenarios:
    results = run_scenario(scenario, args.runs or scenario.repetitions)
    aggregated = aggregate_results(scenario.id, scenario.description, results)
    all_aggregated.append(aggregated)

  write_json_report(all_aggregated, args.output, repetitions=args.runs)
  print_terminal_summary(all_aggregated)
  print(f'Report written to {args.output}.')
  return 0


if __name__ == '__main__':
  raise SystemExit(main())
