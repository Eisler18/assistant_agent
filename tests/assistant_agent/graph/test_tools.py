
from assistant_agent.graph import tools

# ------------------------------------------------------------------ #
# Generic Tool tests                                                 #
# ------------------------------------------------------------------ #
def test_tools_have_descriptions():
  tool_list = [
    tools.create_task,
    tools.get_task,
    tools.parse_date,
    tools.delete_task,
    tools.parse_date_range,
    tools.update_task,
    tools.build_overdue_filter,
    tools.list_tasks,
    tools.build_today_filter,
    tools.build_unscheduled_filter,
    tools.get_daily_briefing_data,
    tools.generate_calendar_link
  ]

  for tool in tool_list:
    assert tool.description


# ------------------------------------------------------------------ #
# Time-related Tool tests                                            #
# ------------------------------------------------------------------ #
def test_parse_date_range_tool():
  parsed_range = tools.parse_date_range.invoke({
    'expression': 'this Monday',
    'end_expression': 'this Friday',
  })
  assert isinstance(parsed_range, dict)
  assert { 'start_time', 'end_time' }.issubset(parsed_range.keys())

def test_build_overdue_filter_tool():
  overdue = tools.build_overdue_filter.invoke({})
  assert isinstance(overdue, dict)
  assert { 'deadline_lte', 'status' }.issubset(overdue.keys())

def test_build_today_filter_tool():
  today = tools.build_today_filter.invoke({})
  assert isinstance(today, dict)
  assert { 'planned_at_gte', 'planned_at_lte' }.issubset(today.keys())

def test_build_unscheduled_filter_tool():
  unscheduled = tools.build_unscheduled_filter.invoke({})
  assert isinstance(unscheduled, dict)
  assert { 'has_deadline', 'has_planned_at' }.issubset(unscheduled.keys())
