# Coding Conventions

This document describes the coding patterns and conventions used in this project. This is an **educational codebase** — some patterns are intentionally imperfect to serve as learning exercises.

---

## File Organization

```
python-flask-main/
├── src/
│   └── main.py          # Application entry point — all routes, DB logic, config
├── test/
│   └── test_tasks.py    # Integration tests for the API
├── docs/                 # Project documentation
├── requirements.txt      # Python dependencies (pinned versions)
└── README.md
```

- **Single-module design**: All application code lives in `src/main.py` (no separate models, services, or routers).
- **Flat test directory**: All tests live in `test/` with the `test_` prefix convention required by pytest.
- **Documentation**: Markdown files in `docs/`.

---

## Database Access Pattern

### Connection Management

The project uses **direct `sqlite3`** — no ORM (no SQLAlchemy, no Peewee).

```python
import sqlite3

DATABASE_PATH = "tasks.db"  # Hard-coded path

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enables dict-like access on rows
    return conn
```

Key characteristics:
- **`get_db_connection()`** is called in every endpoint — no connection pooling or dependency injection.
- **`sqlite3.Row`** row factory allows accessing columns by name (e.g., `row["title"]`).
- Connections are **not closed** after use (intentional bug for educational purposes — see [Known Anti-Patterns](#known-anti-patterns)).

### Schema Initialization

The database schema is initialized on application startup via the `@app.on_event("startup")` lifecycle hook:

```python
@app.on_event("startup")
async def startup():
    init_db()
```

`init_db()` uses `CREATE TABLE IF NOT EXISTS` for idempotent schema creation.

### Query Style

- **Parameterized queries** (`?` placeholders) are used for most operations:
  ```python
  conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
  conn.execute("INSERT INTO tasks (title, description) VALUES (?, ?)", (title, description))
  ```
- **Boolean handling**: SQLite stores booleans as integers (`0`/`1`). Conversion is done inline:
  ```python
  (1 if completed else 0,)
  ```
- **Dynamic UPDATE construction**: The `update_task` endpoint builds SET clauses dynamically from non-None parameters using a list of update fragments and a parallel params list.

---

## Endpoint Conventions

### Framework

The project uses **FastAPI** (`fastapi==0.104.1`) served by **Uvicorn** (`uvicorn==0.24.0`).

### Input via Query Parameters

All endpoint inputs are received as **query parameters**, not JSON request bodies:

```python
@app.post("/tasks")
async def create_task(title: str, description: str = ""):
    ...

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, title: str = None, description: str = None, completed: bool = None):
    ...
```

- `POST /tasks?title=My+Task&description=Details`
- `PUT /tasks/1?title=Updated+Title&completed=true`

This is **unconventional** for REST APIs (JSON bodies are standard for POST/PUT) but is the consistent pattern in this codebase.

### Response Format

All endpoints return **plain dicts** — no Pydantic response models:

```python
return dict(task)               # Single resource
return [dict(t) for t in tasks] # List of resources
return {"message": "..."}       # Action confirmation
```

- `sqlite3.Row` objects are converted to dicts via `dict(row)`.
- No envelope wrapping (e.g., no `{"data": [...], "meta": {...}}`).
- `response_model=List[dict]` is declared on the list endpoint but has no structural enforcement.

### Route Structure

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health/info endpoint |
| GET | `/tasks` | List all tasks (optional `?completed=` filter) |
| GET | `/tasks/{task_id}` | Get single task |
| POST | `/tasks` | Create task |
| PUT | `/tasks/{task_id}` | Update task fields |
| DELETE | `/tasks/{task_id}` | Delete task |
| POST | `/tasks/{task_id}/complete` | Mark task completed |

### Error Handling

- **Minimal**: Only one `HTTPException` exists — a `400` when `update_task` receives no fields to update.
- **No 404 responses**: Getting or updating a non-existent task will raise an unhandled error (intentional — see [Known Anti-Patterns](#known-anti-patterns)).
- No global exception handler or middleware.

---

## Testing Conventions

### Framework & Tools

- **pytest** (`pytest==7.4.3`) as the test runner.
- **FastAPI `TestClient`** (backed by `httpx==0.25.1`) for integration testing.
- Tests are in `test/test_tasks.py`, following pytest's `test_` naming convention.

### Test Structure

Each test function follows this pattern:

```python
def test_<action>(client):
    # Setup — create prerequisite data via API calls
    create_response = client.post("/tasks", params={"title": "Test"})
    task_id = create_response.json()["id"]

    # Action — perform the operation under test
    response = client.put(f"/tasks/{task_id}", params={"title": "Updated"})

    # Assert — verify status code and response data
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
```

### Key Patterns

- **Query params via `params=`**: Tests pass input as `params={"key": "value"}`, matching the endpoint convention.
- **Fixture-based client**: Tests expect a `client` fixture, but it is **commented out** (intentional bug — see [Known Anti-Patterns](#known-anti-patterns)).
- **No database isolation**: Tests share database state. There is no cleanup between tests and no separate test database.
- **No mocking**: All tests are integration tests that hit the real application stack. No unit tests or mocked dependencies.
- **Self-contained setup**: Tests that need data create it inline via API calls before asserting.

---

## Configuration

- **Hard-coded values**: `DATABASE_PATH` and the Uvicorn port (`8000`) are hard-coded in `src/main.py`.
- **No environment variables**: No `.env` file, no `os.getenv()`, no config module.
- **Dependencies pinned** in `requirements.txt` with exact versions.

---

## Known Anti-Patterns

> ⚠️ **These are intentional.** This is an educational codebase where certain bugs and bad practices are left in place as learning exercises. Do not "fix" them without explicit instruction.

| Anti-Pattern | Location | Description |
|---|---|---|
| **SQL injection vulnerability** | `src/main.py` line 153 | `delete_task` uses an f-string (`f"DELETE FROM tasks WHERE id = {task_id}"`) instead of a parameterized query. |
| **Unclosed database connections** | `src/main.py` — every endpoint | `get_db_connection()` opens a connection but callers never call `conn.close()`. This is a resource/memory leak. |
| **Missing 404 error handling** | `src/main.py` — `get_task`, `update_task`, `complete_task`, `delete_task` | Endpoints do not check whether the target task exists before operating on it. |
| **No input validation** | `src/main.py` — `create_task` | Empty string titles are accepted. No length limits. |
| **Commented-out test fixture** | `test/test_tasks.py` lines 22-24 | The `client` pytest fixture is commented out, so all tests referencing it will fail. |
| **No test isolation** | `test/test_tasks.py` | Tests share a single database with no cleanup, causing order-dependent failures. |
| **Hard-coded configuration** | `src/main.py` lines 19, 180 | Database path and server port are hard-coded instead of read from environment/config. |
| **Deprecated startup event** | `src/main.py` line 45 | `@app.on_event("startup")` is deprecated in newer FastAPI versions in favor of lifespan handlers. |
