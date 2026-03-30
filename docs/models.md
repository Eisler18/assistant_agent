# Models

This document describes the core data models used in the Assistant Agent.

## Task

The `Task` model represents a single task in the time management assistant system.

### Overview

The Task entity is the fundamental unit of work in the system. It manages task metadata, lifecycle states, and automatic validation/transformation of task data.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID4 | No | Unique identifier. Auto-generated on creation. Immutable. |
| `title` | str | Yes | Task title. Must not be empty after stripping whitespace. |
| `description` | str \| None | No | Optional detailed description of the task. |
| `deadline` | date \| None | No | Optional deadline date for task completion. |
| `planned_date` | date \| None | No | Optional planned date when the task will be worked on. |
| `estimated_minutes` | int \| None | No | Estimated effort in minutes. Must be positive. Automatically rounded to nearest 15-minute increment. |
| `status` | TaskStatus | No | Current lifecycle state. Defaults to `PENDING`. |
| `created_at` | datetime | No | Timestamp when the task was created. Immutable. |
| `updated_at` | datetime | No | Timestamp of last update. Auto-updated on modifications. |
| `completed_at` | datetime \| None | No | Timestamp when the task was marked as completed. Automatically managed. |

### Class Diagram

```mermaid
---
title: Task Model Class Diagram
---
classDiagram
    class TaskStatus {
        <<enumeration>>
        PENDING
        COMPLETED
        DELETED
    }
    
    class Task {
        -id: UUID4
        -title: str
        -description: str | None
        -deadline: date | None
        -planned_date: date | None
        -estimated_minutes: int | None
        -status: TaskStatus
        -created_at: datetime
        -updated_at: datetime
        -completed_at: datetime | None
        
        +create(kwargs) Task
        +update(kwargs) Task
        +delete() Task
        +to_dict() dict
        +from_dict(data) Task
        -not_empty_title(v) str
        -positive_integer(v) int
        -_completed_at_consistency() Task
        -_round_estimated_minutes() Task
        -_strip_title() Task
    }
    
    Task "1" --> "1" TaskStatus : uses
```

### TaskStatus Enum

Defines the possible lifecycle states of a task:

- **PENDING** (`'pending'`): Default state. Task is awaiting completion.
- **COMPLETED** (`'completed'`): Task has been completed.
- **DELETED** (`'deleted'`): Task has been deleted/archived.

```mermaid
---
title: Task lifecycle
---
stateDiagram-v2
    [*] --> Pending
    Pending --> Completed
    Pending --> Deleted
    Completed --> [*]
    Deleted  --> [*]
```

### Validation Rules

The Task model enforces the following validation rules:

1. **Title Validation**: Title must not be empty after stripping whitespace.
2. **Estimated Minutes Validation**: If provided, must be a positive integer (> 0).
3. **Completed Date Consistency**: 
   - If status is `COMPLETED` and `completed_at` is None, it's automatically set to current UTC time.
   - If status is not `COMPLETED` but `completed_at` is not None, it's automatically cleared.
4. **Estimated Minutes Rounding**: Estimated minutes are automatically rounded up to the nearest 15-minute increment.
5. **Title Stripping**: Title is automatically stripped of leading/trailing whitespace.

### Usage Examples

#### Creating a Task

```python
from assistant_agent.models.task import Task

# Basic task creation
task = Task.create(title="Implement feature X")

# Task with full details
task = Task.create(
    title="Submit report",
    description="Submit quarterly report to management",
    deadline=date(2026, 4, 15),
    estimated_minutes=120
)
```

#### Updating a Task

```python
# Update task fields (except id and created_at which cannot be modified)
updated_task = task.update(
    status=TaskStatus.COMPLETED,
    description="Updated description"
)
```

#### Marking a Task as Deleted

```python
deleted_task = task.delete()  # Sets status to DELETED
```

#### Serialization

```python
# Convert to dictionary
task_dict = task.to_dict()

# Create from dictionary
task = Task.from_dict(task_dict)
```

### Important Behaviors

- **Auto-rounding**: Estimated minutes are rounded to 15-minute intervals for consistent scheduling.
- **Immutable Fields**: `id` and `created_at` cannot be modified after creation.
- **Auto-completion Tracking**: When a task is marked as completed, the completion timestamp is automatically recorded.
- **Updated Tracking**: The `updated_at` field is automatically updated whenever the task is modified via the `update()` method.
