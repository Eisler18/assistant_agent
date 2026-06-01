from datetime import UTC, datetime, timedelta
from pathlib import Path
import json
from typing import Any

TASK_IDS = {
  'overdue': '78bae885-a9a2-40f1-9081-a5047e9c9694',
  'today_prep': '48938062-9c3c-405d-9389-70273d15eac5',
  'tomorrow_workout': '17277980-fc5b-4335-8033-56c433e7f9b6',
  'unscheduled_presentation': '61d8d1dc-4eda-46d3-bbe4-6cfa10fdbee9',
  'upcoming_talk': '95f1db80-02b1-455e-b131-f090627eaa31',
  'completed_review': '0983197f-bcaf-4843-af2e-e3363b283d31',
  'plain_pending': 'd58c87f8-3826-40e8-9829-c61deee2b8cf'
}

def _iso(value: datetime | None) -> str | None:
  if value is None:
    return None
  return value.astimezone(UTC).isoformat()

def generate_seed() -> dict[str, dict[str, Any]]:
  now = datetime.now(UTC)
  today_10 = now.replace(hour=10, minute=0, second=0, microsecond=0)
  tomorrow_9 = today_10 + timedelta(days=1, hours=-1)
  completed_at = now - timedelta(days=7)

  tasks = {
    TASK_IDS['overdue']: {
      'id': TASK_IDS['overdue'],
      'title': 'Overdue Report',
      'description': 'Compile the overdue report',
      'status': 'pending',
      'deadline': _iso(now - timedelta(days=2)),
      'planned_at': None,
      'estimated_minutes': None,
      'created_at': _iso(now - timedelta(days=10)),
      'updated_at': _iso(now - timedelta(days=2)),
      'completed_at': None
    },
    TASK_IDS['today_prep']: {
      'id': TASK_IDS['today_prep'],
      'title': "Today's Meeting Prep",
      'description': 'Prepare notes for today',
      'status': 'pending',
      'deadline': _iso(now + timedelta(days=7)),
      'planned_at': _iso(today_10),
      'estimated_minutes': 60,
      'created_at': _iso(now - timedelta(days=3)),
      'updated_at': _iso(now - timedelta(days=1)),
      'completed_at': None
    },
    TASK_IDS['tomorrow_workout']: {
      'id': TASK_IDS['tomorrow_workout'],
      'title': 'Tomorrow Workout',
      'description': 'Morning run',
      'status': 'pending',
      'deadline': None,
      'planned_at': _iso(tomorrow_9),
      'estimated_minutes': 45,
      'created_at': _iso(now - timedelta(days=1)),
      'updated_at': _iso(now - timedelta(days=1)),
      'completed_at': None
    },
    TASK_IDS['unscheduled_presentation']: {
      'id': TASK_IDS['unscheduled_presentation'],
      'title': 'Unscheduled Presentation',
      'description': 'Draft slides',
      'status': 'pending',
      'deadline': _iso(now + timedelta(days=5)),
      'planned_at': None,
      'estimated_minutes': None,
      'created_at': _iso(now - timedelta(days=2)),
      'updated_at': _iso(now - timedelta(days=2)),
      'completed_at': None
    },
    TASK_IDS['upcoming_talk']: {
      'id': TASK_IDS['upcoming_talk'],
      'title': 'Upcoming Conference Talk',
      'description': 'Prepare talk outline',
      'status': 'pending',
      'deadline': _iso(now + timedelta(days=10)),
      'planned_at': _iso(now + timedelta(days=5)),
      'estimated_minutes': 90,
      'created_at': _iso(now - timedelta(days=4)),
      'updated_at': _iso(now - timedelta(days=2)),
      'completed_at': None
    },
    TASK_IDS['completed_review']: {
      'id': TASK_IDS['completed_review'],
      'title': 'Completed Literature Review',
      'description': 'Review related work',
      'status': 'completed',
      'deadline': None,
      'planned_at': _iso(completed_at),
      'estimated_minutes': 120,
      'created_at': _iso(completed_at - timedelta(days=1)),
      'updated_at': _iso(completed_at),
      'completed_at': _iso(completed_at)
    },
    TASK_IDS['plain_pending']: {
      'id': TASK_IDS['plain_pending'],
      'title': 'Plain Pending Task',
      'description': 'Simple task',
      'status': 'pending',
      'deadline': None,
      'planned_at': None,
      'estimated_minutes': None,
      'created_at': _iso(now - timedelta(days=6)),
      'updated_at': _iso(now - timedelta(days=3)),
      'completed_at': None
    }
  }

  return tasks

def write_seed(output_path: Path) -> None:
  output_path.parent.mkdir(parents=True, exist_ok=True)
  payload = generate_seed()
  with open(output_path, 'w', encoding='utf-8') as handle:
    json.dump(payload, handle, indent=2)
