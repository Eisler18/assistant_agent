from __future__ import annotations
# pylint: skip-file

from datetime import datetime, timezone
import os
from pathlib import Path
import json
import statistics
import math
from typing import Any


def aggregate_results(scenario_id: str, description: str, results: list) -> dict[str, Any]:
  runs_detail: list[dict[str, Any]] = []
  assertion_stats: dict[str, dict[str, int]] = {}
  errors = 0

  token_values: list[float] = []
  latencies: list[float] = []

  for run in results:
    if run.error:
      errors += 1

    run_assertions = []
    for a in run.assertions:
      run_assertions.append({ 'name': a.name, 'passed': a.passed, 'detail': a.detail })
      stats = assertion_stats.setdefault(a.name, { 'passed': 0, 'failed': 0 })
      if a.passed:
        stats['passed'] += 1
      else:
        stats['failed'] += 1

    runs_detail.append({
      'run_index': run.run_index,
      'error': run.error,
      'assertions': run_assertions,
      'langsmith': run.langsmith_data,
    })

    if run.langsmith_data:
      lt = run.langsmith_data.get('latency_ms')
      tt = run.langsmith_data.get('total_tokens')
      if isinstance(tt, (int, float)):
        token_values.append(tt)
      if isinstance(lt, (int, float)):
        latencies.append(lt)

  total_runs = len(results)

  assertions_aggregated = []
  for name, stats in assertion_stats.items():
    passed = stats.get('passed', 0)
    failed = stats.get('failed', 0)
    pass_rate = passed / total_runs if total_runs else 0.0
    assertions_aggregated.append({
      'name': name,
      'passed': passed,
      'failed': failed,
      'pass_rate': pass_rate,
    })

  langsmith_summary = None
  if token_values or latencies:
    langsmith_summary = {}
    if token_values:
      langsmith_summary['mean_tokens'] = statistics.mean(token_values)
      if len(token_values) > 1:
        try:
          langsmith_summary['std_tokens'] = statistics.stdev(token_values)
        except Exception:
          langsmith_summary['std_tokens'] = None
    if latencies:
      lat_sorted = sorted(latencies)
      langsmith_summary['p50_latency_ms'] = statistics.median(lat_sorted)
      idx = min(len(lat_sorted) - 1, math.ceil(0.95 * len(lat_sorted)) - 1)
      langsmith_summary['p95_latency_ms'] = lat_sorted[idx]

  return {
    'id': str(scenario_id),
    'description': description,
    'runs': total_runs,
    'errors': errors,
    'runs_detail': runs_detail,
    'assertions': assertions_aggregated,
    'langsmith': langsmith_summary,
  }


def write_json_report(all_aggregated: list[dict], output_path: Path, repetitions: int | None = None) -> None:
  model = os.getenv('LLM_MODEL_NAME', 'unknown')
  
  payload = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'model': model or 'unknown',
    'repetitions': repetitions,
    'scenarios': all_aggregated,
  }

  total = len(all_aggregated)
  fully_passing = 0
  partial = 0
  errored = 0
  pass_rates: list[float] = []
  for s in all_aggregated:
    if s.get('errors', 0) > 0:
      errored += 1
    aps = [a.get('pass_rate', 0.0) for a in s.get('assertions', [])]
    if not aps:
      scenario_rate = 1.0
    else:
      scenario_rate = sum(aps) / len(aps)
    pass_rates.append(scenario_rate)
    if scenario_rate >= 1.0 and s.get('errors', 0) == 0:
      fully_passing += 1
    elif scenario_rate < 1.0 and s.get('errors', 0) == 0:
      partial += 1

  overall_assertion_pass_rate = sum(pass_rates) / len(pass_rates) if pass_rates else 1.0

  payload['summary'] = {
    'total_scenarios': total,
    'fully_passing': fully_passing,
    'partial': partial,
    'errored': errored,
    'overall_assertion_pass_rate': overall_assertion_pass_rate,
  }

  output_path.parent.mkdir(parents=True, exist_ok=True)
  with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)


def print_terminal_summary(all_aggregated: list[dict]) -> None:
  rows = []
  for s in all_aggregated:
    runs = s.get('runs', 0)
    errors = s.get('errors', 0)
    aps = [a.get('pass_rate', 0.0) for a in s.get('assertions', [])]
    scenario_rate = sum(aps) / len(aps) if aps else 1.0
    mean_tokens = s.get('langsmith', {}).get('mean_tokens') if s.get('langsmith') else None
    p50 = s.get('langsmith', {}).get('p50_latency_ms') if s.get('langsmith') else None
    rows.append((s.get('id'), runs, errors, scenario_rate, mean_tokens, p50))

  print('Scenario summary:')
  print('scenario | runs | errors | pass_rate | mean_tokens | p50_ms')
  for r in rows:
    print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]:.2f} | {r[4] or '-'} | {r[5] or '-'}")
