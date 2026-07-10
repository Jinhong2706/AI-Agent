---
name: tasks
description: Use this skill when the user asks to create, modify, update, view, delete, pause, or resume scheduled tasks or reminders. Also use when the user asks about task results, wants to check what tasks are running, or asks 'what tasks do I have?'. Triggers on 'create a reminder', 'schedule a task', 'remind me every', 'check my tasks', 'update task', 'edit task', 'change task', 'delete task', 'pause task', 'task results', 'what did my task find', or any request involving recurring automated Grok actions.
---

# Task Management

Scheduled Grok tasks (reminders and recurring jobs) are exposed as connected tools. Discover them with `search_connected_tools` and invoke them with `call_connected_tool` — the toolbox path forwards the user's auth credentials to the backend.

`task_create` returns a JSON object containing the new `task_id` and the task's `status`. Pass the `task_id` to `task_get_results` / `task_delete` / `task_update`, and use the `schedule_id` (from `task_list`) for `task_pause` or `task_update`.

## Available Tools

{"name": "task_create", "description": "Create a new scheduled task. Returns a JSON object containing task_id and status — store the task_id for follow-up calls (task_get_results, task_delete).", "parameters": {"properties": {"name": {"description": "Short identifier for the task (e.g. 'bitcoin-price-check').", "type": "string"}, "prompt": {"description": "The prompt Grok executes on each run.", "type": "string"}, "cadence": {"description": "RFC 5545 recurrence rule (e.g. 'RRULE:FREQ=DAILY', 'RRULE:FREQ=WEEKLY;BYDAY=MO'). Omit or leave empty for a one-time task. See the Cadence Guide below.", "type": "string"}, "scheduled_date": {"description": "ISO 8601 date for one-time tasks (e.g. '2026-05-25'). Required when cadence is omitted (run-once). Defaults to today.", "type": "string"}, "time_of_day": {"description": "24h time of day. Defaults to '09:00'.", "type": "string"}, "timezone": {"description": "IANA timezone. Defaults to the user's timezone.", "type": "string"}, "notification": {"description": "Notification preference. One of 'default', 'email_only', 'app_only', 'off'.", "type": "string"}}, "required": ["name", "prompt"], "type": "object"}}

{"name": "task_list", "description": "List the user's active tasks with their schedules and recent status. Takes no arguments.", "parameters": {"properties": {}, "type": "object"}}

{"name": "task_update", "description": "Update an existing scheduled task. Use when the user asks to change, edit, or modify a task's name, prompt, schedule, or notification settings. Requires task_id and schedule_id from task_list.", "parameters": {"properties": {"task_id": {"description": "The task_id of the task to update (from task_list).", "type": "string"}, "schedule_id": {"description": "The schedule_id to update (from task_list).", "type": "string"}, "name": {"description": "Updated short identifier for the task.", "type": "string"}, "prompt": {"description": "Updated prompt Grok executes on each run.", "type": "string"}, "cadence": {"description": "RFC 5545 recurrence rule. Omit or leave empty for a one-time task. See the Cadence Guide below.", "type": "string"}, "scheduled_date": {"description": "ISO 8601 date for one-time tasks. Required when cadence is omitted. Defaults to today.", "type": "string"}, "time_of_day": {"description": "24h time of day. Defaults to '09:00'.", "type": "string"}, "timezone": {"description": "IANA timezone. Defaults to the user's timezone.", "type": "string"}, "notification": {"description": "Notification preference. One of 'default', 'email_only', 'app_only', 'off'.", "type": "string"}}, "required": ["task_id", "schedule_id", "name", "prompt"], "type": "object"}}

{"name": "task_delete", "description": "Archive a task so it stops running. Look up the task_id from task_create or task_list. Only use when the user explicitly says 'delete' or 'archive'. If the user says 'stop' or 'cancel', use task_pause instead.", "parameters": {"properties": {"task_id": {"description": "The task_id returned by task_create or surfaced by task_list.", "type": "string"}}, "required": ["task_id"], "type": "object"}}

{"name": "task_pause", "description": "Pause or resume a task schedule. A single task may have multiple schedules; pause acts on a specific schedule_id from task_list.", "parameters": {"properties": {"schedule_id": {"description": "The schedule_id (from task_list) to pause or resume. Note: this is the schedule_id, not the task_id.", "type": "string"}, "is_enabled": {"description": "Set false to pause, true to resume.", "type": "boolean"}}, "required": ["schedule_id", "is_enabled"], "type": "object"}}

{"name": "task_get_results", "description": "Fetch recent execution results for a task.", "parameters": {"properties": {"task_id": {"description": "The task_id whose results to fetch.", "type": "string"}, "limit": {"description": "Maximum number of results to return. Defaults to 5.", "type": "integer"}}, "required": ["task_id"], "type": "object"}}

## Cadence Guide (RFC 5545)

`cadence` is an iCalendar RRULE string — the same format Google Calendar uses.

| Use case | RRULE |
|----------|-------|
| Run once at a specific date/time | omit / empty (set `scheduled_date` to the target date) |
| Every day | `RRULE:FREQ=DAILY` |
| Every weekday (Mon–Fri) | `RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR` |
| Every Monday | `RRULE:FREQ=WEEKLY;BYDAY=MO` |
| 15th of every month | `RRULE:FREQ=MONTHLY;BYMONTHDAY=15` |
| Once a year (anniversary) | `RRULE:FREQ=YEARLY` |

Do **not** include `DTSTART` or `DTEND` in the RRULE; supply the time using `time_of_day` and `timezone` instead.

## Workflow

1. **Creating**: Ask the user for prompt, cadence, and time. Call `task_create` through `call_connected_tool`, then surface the returned `task_id`/`status` to the user.
2. **Listing**: Call `task_list` and present tasks with their `name`, cadence, next run time, and status.
3. **Updating**: List tasks first to get the `task_id` and `schedule_id`, then call `task_update` with the updated fields.
4. **Modifying**: List tasks first to get the `task_id` (or `schedule_id` for pause), then call `task_pause` / `task_delete`.
5. **Results**: Call `task_get_results` to show what a task produced.

## Agent Rules

1. Always invoke task tools through `call_connected_tool` with the correct `tool_name` and `arguments`.
2. Create tasks directly without asking for confirmation -- the user can always manage tasks from the Tasks page.
3. When listing tasks, present them in a readable format with name, cadence, next run time, and status.
4. When the user says "remind me", "check every day", or similar, create a task with the appropriate cadence.
5. Default to `RRULE:FREQ=DAILY` and `09:00` if the user doesn't specify cadence/time.
6. Default to the user's timezone if not specified.
