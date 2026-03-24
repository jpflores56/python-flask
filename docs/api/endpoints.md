# API Reference — Task Manager API

> **Base URL:** `http://localhost:8000`
> **Framework:** FastAPI (Python)
> **Database:** SQLite

## Table of Contents

- [Overview](#overview)
- [Task Object Schema](#task-object-schema)
- [Endpoints](#endpoints)
  - [GET / — Health Check](#get----health-check)
  - [GET /tasks — List Tasks](#get-tasks--list-tasks)
  - [GET /tasks/{task_id} — Get Task](#get-taskstask_id--get-task)
  - [POST /tasks — Create Task](#post-tasks--create-task)
  - [PUT /tasks/{task_id} — Update Task](#put-taskstask_id--update-task)
  - [DELETE /tasks/{task_id} — Delete Task](#delete-taskstask_id--delete-task)
  - [POST /tasks/{task_id}/complete — Complete Task](#post-taskstask_idcomplete--complete-task)
- [Global Known Issues](#global-known-issues)

---

## Overview

The Task Manager API provides CRUD operations for managing tasks stored in a SQLite database. The API runs on port `8000` by default.

> **⚠️ Important:** `POST` and `PUT` endpoints accept parameters as **query parameters**, _not_ as a JSON request body.

---

## Task Object Schema

All endpoints that return a task use the following JSON structure (serialized from an `sqlite3.Row`):

```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "completed": 0,
  "created_at": "2024-01-01 12:00:00"
}
```

| Field        | Type      | Description                                      |
|--------------|-----------|--------------------------------------------------|
| `id`         | `integer` | Auto-incrementing primary key                    |
| `title`      | `string`  | Task title (NOT NULL)                            |
| `description`| `string`  | Task description (nullable)                      |
| `completed`  | `integer` | Completion flag: `0` = incomplete, `1` = complete|
| `created_at` | `string`  | ISO-style timestamp, set by SQLite on creation   |

> **Note:** `completed` is stored as an integer (`0`/`1`), not a boolean, because SQLite has no native boolean type.

---

## Endpoints

### GET `/` — Health Check

Returns a static message confirming the API is running.

**Parameters:** None

**Response Schema:**

```json
{
  "message": "Task Manager API",
  "version": "1.0.0"
}
```

| Field     | Type     | Description                  |
|-----------|----------|------------------------------|
| `message` | `string` | Always `"Task Manager API"`  |
| `version` | `string` | Always `"1.0.0"`            |

**Status Codes:**

| Code | Description     |
|------|-----------------|
| 200  | Success         |

**curl Example:**

```bash
curl http://localhost:8000/
```

**Known Issues:** None.

---

### GET `/tasks` — List Tasks

Returns all tasks, optionally filtered by completion status. Results are ordered by `created_at DESC`.

**Query Parameters:**

| Parameter   | Type            | Required | Default | Description                                     |
|-------------|-----------------|----------|---------|-------------------------------------------------|
| `completed` | `boolean`       | No       | `null`  | Filter by completion status. Omit to return all.|

**Response Schema:**

```json
[
  {
    "id": 1,
    "title": "string",
    "description": "string",
    "completed": 0,
    "created_at": "2024-01-01 12:00:00"
  }
]
```

Returns an array of [Task objects](#task-object-schema). May be empty (`[]`).

**Status Codes:**

| Code | Description     |
|------|-----------------|
| 200  | Success         |

**curl Examples:**

```bash
# List all tasks
curl http://localhost:8000/tasks

# List only completed tasks
curl "http://localhost:8000/tasks?completed=true"

# List only incomplete tasks
curl "http://localhost:8000/tasks?completed=false"
```

**Known Issues:**
- Database connection is never closed after query (memory leak).
- No pagination support — returns all matching tasks at once.

---

### GET `/tasks/{task_id}` — Get Task

Returns a single task by its ID.

**Path Parameters:**

| Parameter | Type      | Required | Description                |
|-----------|-----------|----------|----------------------------|
| `task_id` | `integer` | Yes      | The ID of the task to get  |

**Response Schema:**

```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "completed": 0,
  "created_at": "2024-01-01 12:00:00"
}
```

Returns a single [Task object](#task-object-schema).

**Status Codes:**

| Code | Description                                                 |
|------|-------------------------------------------------------------|
| 200  | Success                                                     |
| 422  | Validation error (e.g., `task_id` is not an integer)        |

> **⚠️ Missing:** No `404` response is returned when `task_id` does not exist — the server crashes with an internal error instead.

**curl Example:**

```bash
curl http://localhost:8000/tasks/1
```

**Known Issues:**
- **No 404 handling.** If the task does not exist, `dict(task)` is called on `None`, raising an unhandled `TypeError` which results in a `500 Internal Server Error`.
- Database connection is never closed (memory leak).

---

### POST `/tasks` — Create Task

Creates a new task and returns it.

> **⚠️ Parameters are passed as query parameters, not a JSON body.**

**Query Parameters:**

| Parameter     | Type     | Required | Default | Description           |
|---------------|----------|----------|---------|-----------------------|
| `title`       | `string` | Yes      | —       | The title of the task |
| `description` | `string` | No       | `""`    | Task description      |

**Response Schema:**

```json
{
  "id": 2,
  "title": "string",
  "description": "string",
  "completed": 0,
  "created_at": "2024-01-01 12:00:00"
}
```

Returns the newly created [Task object](#task-object-schema) with its assigned `id`.

**Status Codes:**

| Code | Description                                              |
|------|----------------------------------------------------------|
| 200  | Task created successfully                                |
| 422  | Validation error (e.g., missing required `title` param)  |

**curl Examples:**

```bash
# Create a task with title only
curl -X POST "http://localhost:8000/tasks?title=Buy%20groceries"

# Create a task with title and description
curl -X POST "http://localhost:8000/tasks?title=Buy%20groceries&description=Milk%2C%20eggs%2C%20bread"
```

**Known Issues:**
- **No empty title validation.** An empty string (`title=`) is accepted, creating a task with a blank title.
- Uses query parameters instead of a JSON request body, which is non-standard for `POST` endpoints.
- Database connection is never closed (memory leak).

---

### PUT `/tasks/{task_id}` — Update Task

Updates one or more fields on an existing task. At least one field must be provided.

> **⚠️ Parameters are passed as query parameters, not a JSON body.**

**Path Parameters:**

| Parameter | Type      | Required | Description                   |
|-----------|-----------|----------|-------------------------------|
| `task_id` | `integer` | Yes      | The ID of the task to update  |

**Query Parameters:**

| Parameter     | Type      | Required | Default | Description                      |
|---------------|-----------|----------|---------|----------------------------------|
| `title`       | `string`  | No       | `null`  | New title for the task           |
| `description` | `string`  | No       | `null`  | New description for the task     |
| `completed`   | `boolean` | No       | `null`  | New completion status            |

> At least one of `title`, `description`, or `completed` must be provided.

**Response Schema:**

```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "completed": 1,
  "created_at": "2024-01-01 12:00:00"
}
```

Returns the updated [Task object](#task-object-schema).

**Status Codes:**

| Code | Description                                           |
|------|-------------------------------------------------------|
| 200  | Task updated successfully                             |
| 400  | No update fields provided (`"No fields to update"`)   |
| 422  | Validation error (e.g., `task_id` is not an integer)  |

> **⚠️ Missing:** No `404` response is returned when `task_id` does not exist. The update query silently succeeds, then the subsequent `SELECT` on a non-existent row crashes with a `500 Internal Server Error`.

**curl Examples:**

```bash
# Update the title only
curl -X PUT "http://localhost:8000/tasks/1?title=Updated%20Title"

# Update multiple fields
curl -X PUT "http://localhost:8000/tasks/1?title=New%20Title&completed=true"

# Mark a task as incomplete
curl -X PUT "http://localhost:8000/tasks/1?completed=false"
```

**Known Issues:**
- **No 404 handling.** If the task does not exist, the `UPDATE` succeeds silently (0 rows affected), but the subsequent `SELECT` returns `None`, crashing with a `TypeError`.
- Uses query parameters instead of a JSON request body, which is non-standard for `PUT` endpoints.
- Database connection is never closed (memory leak).

---

### DELETE `/tasks/{task_id}` — Delete Task

Deletes a task by its ID.

**Path Parameters:**

| Parameter | Type      | Required | Description                    |
|-----------|-----------|----------|--------------------------------|
| `task_id` | `integer` | Yes      | The ID of the task to delete   |

**Response Schema:**

```json
{
  "message": "Task deleted successfully"
}
```

| Field     | Type     | Description                               |
|-----------|----------|-------------------------------------------|
| `message` | `string` | Always `"Task deleted successfully"`      |

**Status Codes:**

| Code | Description                                            |
|------|--------------------------------------------------------|
| 200  | Task deleted (or no-op if `task_id` did not exist)     |
| 422  | Validation error (e.g., `task_id` is not an integer)   |

> **⚠️ Missing:** No `404` response if the task does not exist — the `DELETE` silently succeeds and returns `200`.

**curl Example:**

```bash
curl -X DELETE http://localhost:8000/tasks/1
```

**Known Issues:**
- **🔴 CRITICAL: SQL injection vulnerability.** The query is built via f-string interpolation (`f"DELETE FROM tasks WHERE id = {task_id}"`). Although FastAPI's path parameter typing provides _some_ protection by validating `task_id` as an `int`, the use of string interpolation instead of parameterized queries is a severe security anti-pattern. The safe alternative is: `"DELETE FROM tasks WHERE id = ?"`, `(task_id,)`.
- No 404 handling — always returns `200` even if the task did not exist.
- Database connection is never closed (memory leak).

---

### POST `/tasks/{task_id}/complete` — Complete Task

Marks a task as completed by setting `completed = 1`.

**Path Parameters:**

| Parameter | Type      | Required | Description                     |
|-----------|-----------|----------|---------------------------------|
| `task_id` | `integer` | Yes      | The ID of the task to complete  |

**Response Schema:**

```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "completed": 1,
  "created_at": "2024-01-01 12:00:00"
}
```

Returns the updated [Task object](#task-object-schema) with `completed` set to `1`.

**Status Codes:**

| Code | Description                                           |
|------|-------------------------------------------------------|
| 200  | Task marked as complete                               |
| 422  | Validation error (e.g., `task_id` is not an integer)  |

> **⚠️ Missing:** No `404` response is returned when `task_id` does not exist. The `UPDATE` silently succeeds, then the `SELECT` on a non-existent row crashes with a `500 Internal Server Error`.

**curl Example:**

```bash
curl -X POST http://localhost:8000/tasks/1/complete
```

**Known Issues:**
- **No 404 handling.** Same pattern as other endpoints — crashes if task does not exist.
- No idempotency concern (completing an already-completed task is harmless but unreported).
- Database connection is never closed (memory leak).

---

## Global Known Issues

These issues affect multiple or all endpoints:

| Issue                            | Severity | Affected Endpoints                           | Description                                                                                 |
|----------------------------------|----------|----------------------------------------------|---------------------------------------------------------------------------------------------|
| Database connection leak         | Medium   | All except `GET /`                           | `get_db_connection()` opens a new connection per request but never closes it.                |
| Missing 404 handling             | High     | `GET`, `PUT`, `POST .../complete` on tasks   | Endpoints crash with `500` when accessing a non-existent `task_id`.                         |
| SQL injection in DELETE          | Critical | `DELETE /tasks/{task_id}`                    | Uses f-string interpolation instead of parameterized queries.                               |
| No empty title validation        | Low      | `POST /tasks`                                | Accepts empty string as a valid title.                                                      |
| Query params instead of body     | Low      | `POST /tasks`, `PUT /tasks/{task_id}`        | Non-standard API design; should accept JSON request body for create/update operations.      |
| No pagination                    | Low      | `GET /tasks`                                 | Returns all matching tasks with no limit/offset support.                                    |
| Hard-coded configuration         | Low      | All                                          | Database path and server port are hard-coded in source.                                     |
