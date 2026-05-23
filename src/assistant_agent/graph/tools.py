
from datetime import UTC, datetime, timedelta
from langchain_core.tools import tool
from ..models import Task
from ..repository import TaskFilter
from ..utils.date_parser import (
  coerce_datetime,
  format_datetime,
  get_day_bounds,
  get_today_bounds
)

def _initialize_task(
  title: str,
  description: str | None = None,
  planned_at: str | None = None,
  deadline: str | None = None,
  estimated_minutes: int | None = None,
) -> Task:
  planned_at_dt = coerce_datetime(planned_at)
  deadline_dt = coerce_datetime(deadline)

  task = Task.new(
    title=title,
    description=description,
    planned_at=planned_at_dt,
    deadline=deadline_dt,
    estimated_minutes=estimated_minutes
  )
  return task

@tool
def format_task_preview(tasks: list[dict]) -> str:
  '''Format a user-facing task preview string from a task dict.

  Returns: string with title, planned_at, deadline, estimated_minutes, status.
  Example:
    Task preview:\n  Title: Write report\n  Planned: 2026-05-20 10:00 (UTC)
  '''
  if not tasks:
    return 'No tasks found.'

  tasks = [Task.from_dict(task_dict) for task_dict in tasks]
  previews = []
  for task in tasks:
    estimated_minutes = task.estimated_minutes
    estimated_text = 'None' if estimated_minutes is None else f'{estimated_minutes} minutes'
    previews.append(
      f"  Title: {task.title}\n"
      f"  Planned: {format_datetime(task.planned_at)}\n"
      f"  Deadline: {format_datetime(task.deadline)}\n"
      f"  Estimated time: {estimated_text}\n"
      f"  Status: {task.status.capitalize()}"
    )

  return f"{'Tasks' if len(previews) > 1 else 'Task'}:\n" + '\n\n'.join(previews)

# --- Task CRUD --- #
@tool
def new_task(
  title: str,
  *,
  description: str | None = None,
  planned_at: str | None = None,
  deadline: str | None = None,
  estimated_minutes: int | None = None,
) -> dict:
  '''Initialize a task dict without saving to the repository. 
  Useful for confirmation before creation.

  Params: title (str), description (str|None), planned_at (str|None), deadline (str|None),
    estimated_minutes (int|None).
  Returns: dict of the initialized task.
  Example: initialize_task({"title": "Write intro", "deadline": "next Friday"})
  '''
  task = _initialize_task(
    title=title,
    description=description,
    planned_at=planned_at,
    deadline=deadline,
    estimated_minutes=estimated_minutes
  )
  return { 'tasks': [task.to_dict()] }

@tool
def create_task(
  title: str,
  *,
  description: str | None = None,
  planned_at: str | None = None,
  deadline: str | None = None,
  estimated_minutes: int | None = None,
) -> dict:
  '''Create a task.

  Params: title (str), description (str|None), planned_at (str|None), deadline (str|None),
    estimated_minutes (int|None).
  Returns: dict of the created task.
  Example: create_task({"title": "Write intro", "deadline": "next Friday"})
  '''
  task = _initialize_task(
    title=title,
    description=description,
    planned_at=planned_at,
    deadline=deadline,
    estimated_minutes=estimated_minutes
  )
  task = task.save()

  return { 'tasks': [task.to_dict()] }

@tool
def get_task(task_id: str) -> dict:
  '''Fetch a task by ID.

  Params: task_id (str).
  Returns: dict of the task.
  Example: get_task({"task_id": "<uuid>"})
  '''
  try:
    task = Task.find(task_id)
  except KeyError as exc:
    raise ValueError(f'Task with id {task_id} not found') from exc
  return { 'tasks': [task.to_dict()] }

@tool
# pylint: disable=too-many-arguments
def list_tasks(
  *,
  status: str | None = None,
  planned_at_gte: datetime | str | None = None,
  planned_at_lte: datetime | str | None = None,
  deadline_lte: datetime | str | None = None,
  has_deadline: bool | None = None,
  has_planned_at: bool | None = None,
) -> list[dict]:
  '''List tasks using optional filters.

  Params: status (str|None), planned_at_gte (datetime|str|None),
    planned_at_lte (datetime|str|None), deadline_lte (datetime|str|None),
    has_deadline (bool|None), has_planned_at (bool|None).
  Returns: list of task dicts.
  Example: list_tasks({"status": "pending", "planned_at_gte": "today"})
  '''
  query: TaskFilter = {}
  if status is not None:
    query['status'] = status

  planned_at_gte_dt = coerce_datetime(planned_at_gte)
  if planned_at_gte_dt is not None:
    query['planned_at_gte'] = planned_at_gte_dt

  planned_at_lte_dt = coerce_datetime(planned_at_lte)
  if planned_at_lte_dt is not None:
    query['planned_at_lte'] = planned_at_lte_dt

  deadline_lte_dt = coerce_datetime(deadline_lte)
  if deadline_lte_dt is not None:
    query['deadline_lte'] = deadline_lte_dt

  if has_deadline is not None:
    query['has_deadline'] = has_deadline

  if has_planned_at is not None:
    query['has_planned_at'] = has_planned_at

  tasks = Task.search(query)
  if not tasks:
    return 'No tasks found matching the filters.'
  return { 'tasks': [task.to_dict() for task in tasks] }
# pylint: enable=too-many-arguments

# pylint: disable=too-many-arguments
@tool
def update_task(
  task_id: str,
  *,
  title: str | None = None,
  description: str | None = None,
  planned_at: str | None = None,
  deadline: str | None = None,
  estimated_minutes: int | None = None,
  status: str | None = None,
) -> dict:
  '''Update a task's fields.

  Params: task_id (str) plus optional fields (title, description, planned_at, deadline,
    estimated_minutes, status).
  Returns: updated task dict.
  Example: update_task({"task_id": "<uuid>", "status": "completed"})
  '''
  task = Task.find(task_id)
  fields: dict[str, object] = {}
  if title is not None:
    fields['title'] = title
  if description is not None:
    fields['description'] = description
  if planned_at is not None:
    fields['planned_at'] = coerce_datetime(planned_at)
  if deadline is not None:
    fields['deadline'] = coerce_datetime(deadline)
  if estimated_minutes is not None:
    fields['estimated_minutes'] = estimated_minutes
  if status is not None:
    fields['status'] = status

  updated = task.update(**fields)
  return { 'tasks': [updated.to_dict()] }
# pylint: enable=too-many-arguments

@tool
def delete_task(task_id: str) -> dict:
  '''Soft-delete a task by ID (sets status to deleted).

  Params: task_id (str).
  Returns: dict with id, title, status.
  Example: delete_task({"task_id": "<uuid>"})
  '''
  task = Task.find(task_id)
  deleted = task.delete()
  return { 'tasks': [deleted.to_dict()] }


# --- Filter builders --- #
@tool
def parse_date_range(expression: str, end_expression: str | None = None) -> dict:
  '''Parse a date range into UTC boundaries for list filtering.
  If end_expression is not provided, returns a:
   - A single-day range covering the parsed date if expression is a specific day (e.g., "on Monday")
   - A week-long range if expression includes "week" (e.g., "this week")
   - A month-long range if expression includes "month" (e.g., "this month")

  Params: expression (str), end_expression (str|None).
  Returns: dict with start_time and end_time (UTC datetimes).
  Example: parse_date_range({"expression": "this Monday", "end_expression": "this Friday"})
  '''
  start = coerce_datetime(expression)
  if end_expression is None:
    if 'week' in expression.lower():
      start = start - timedelta(days=start.weekday())
      end = start + timedelta(days=6)
    elif 'month' in expression.lower():
      start = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
      last_day = (start.replace(month=start.month % 12 + 1) - timedelta(days=1)).day
      end = start.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    else:
      start, end = get_day_bounds(start)
  else:
    end = coerce_datetime(end_expression) + timedelta(days=1) - timedelta(microseconds=1)

  return {
    'start_time': start,
    'end_time': end
  }

@tool
def build_overdue_filter() -> dict:
  '''Return a filter dict for overdue tasks.

  Returns: {'deadline_lte': <now_utc>, 'status': 'pending'}.
  Example: build_overdue_filter({})
  '''
  return { 'deadline_lte': datetime.now(UTC), 'status': 'pending' }

@tool
def build_today_filter() -> dict:
  '''Return a filter dict for tasks planned for today.

  Returns: {'planned_at_gte': <today_start_utc>, 'planned_at_lte': <today_end_utc>}.
  Example: build_today_filter({})
  '''
  day_start, day_end = get_today_bounds()
  return {
    'planned_at_gte': day_start,
    'planned_at_lte': day_end
  }

@tool
def build_unscheduled_filter() -> dict:
  '''Return a filter dict for unscheduled tasks.

  Returns: {'has_deadline': True, 'has_planned_at': False}.
  Example: build_unscheduled_filter({})
  '''
  return { 'has_deadline': True, 'has_planned_at': False, 'status': 'pending' }

@tool
def build_stale_filter() -> dict:
  '''Return a filter dict for tasks with stale planned dates.

  A task is stale when planned_at < now and status is pending.

  Returns: {'planned_at_lte': <now_utc>, 'status': 'pending'}.
  Example: build_stale_filter({})
  '''
  return { 'planned_at_lte': datetime.now(UTC), 'status': 'pending' }


# --- Briefing --- #
@tool
def get_daily_briefing_data() -> dict:
  '''Return a structured summary of overdue, today, upcoming, and unscheduled tasks.

  Returns: dict with lists of task dicts.
  Example: get_daily_briefing_data({})
  '''
  overdue_filter = build_overdue_filter.invoke({})
  overdue_tasks = Task.search(overdue_filter)

  today_filter = build_today_filter.invoke({})
  today_tasks = Task.search(today_filter)

  upcoming_start = today_filter['planned_at_gte'] + timedelta(days=1)
  upcoming_end = upcoming_start + timedelta(days=7) - timedelta(microseconds=1)
  upcoming_filter: TaskFilter = {
    'planned_at_gte': upcoming_start,
    'planned_at_lte': upcoming_end
  }
  upcoming_tasks = Task.search(upcoming_filter)

  unscheduled_filter = build_unscheduled_filter.invoke({})
  unscheduled_tasks = Task.search(unscheduled_filter)

  stale_filter = build_stale_filter.invoke({})
  stale_tasks = Task.search(stale_filter)

  return {
    'overdue': [task.to_dict() for task in overdue_tasks],
    'today': [task.to_dict() for task in today_tasks],
    'upcoming': [task.to_dict() for task in upcoming_tasks],
    'unscheduled': [task.to_dict() for task in unscheduled_tasks],
    'stale': [task.to_dict() for task in stale_tasks]
  }


# --- Calendar output helpers --- #
@tool
def generate_calendar_link(
  title: str | None = None,
  start_time: str | None = None,
  duration_minutes: int | None = None,
  focus_time: bool = False,
  task_id: str | None = None
) -> str:
  '''Generate a Google Calendar quick-add link for a calendar event.

  Params: title (str|None), start_time (str|None), duration_minutes (int|None),
    focus_time (bool), task_id (str|None).
  Returns: URL string.
  Example: generate_calendar_link({"title": "Write", "start_time": "tomorrow 10am"})
  '''
  _ = (title, start_time, duration_minutes, focus_time, task_id)
  return ''

TASK_READ_TOOLS = [
  list_tasks,
  get_task,
  parse_date_range,
  build_overdue_filter,
  build_today_filter,
  build_unscheduled_filter,
  build_stale_filter,
  format_task_preview
]

TASK_CREATE_TOOLS = [
  create_task,
  new_task,
  format_task_preview
]

TASK_UPDATE_TOOLS = [
  get_task,
  list_tasks,
  update_task,
  delete_task,
  parse_date_range,
  format_task_preview
]

BRIEFING_TOOLS = [
  get_daily_briefing_data,
  format_task_preview
]
