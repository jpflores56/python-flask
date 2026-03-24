# Project: Task Manager API — AI Agent Context

> **⚠️ CRITICAL WARNING: This project contains INTENTIONAL BUGS for educational and AI-assisted workflow testing purposes. Do NOT fix any bugs unless explicitly asked to do so.**

## Project Overview

This is a **FastAPI-based Task Manager API** designed as a sandbox for AI-assisted development workflows. It is a deliberately simple, single-file application (`src/main.py`) with **known bugs intentionally embedded** to test how AI agents detect, report, and fix issues.

- **Framework:** FastAPI (Python)
- **Database:** SQLite via the `sqlite3` standard library module (no ORM)
- **Architecture:** Single-file API — all endpoints, database logic, and configuration live in `src/main.py`
- **Testing:** pytest with `httpx` / `TestClient`

---

## File-to-Concept Mapping

| File | Purpose |
|------|---------|
| `src/main.py` | All API endpoints, database operations, app configuration |
| `src/__init__.py` | Package init (empty) |
| `test/test_tasks.py` | Test suite with intentional failures (commented-out fixture) |
| `test/__init__.py` | Package init (empty) |
| `mcp.md` | MCP governance policy |
| `requirements.txt` | Python dependencies: fastapi, uvicorn, pytest, httpx |
| `README.md` | Project overview and quick reference |
| `CONTRIBUTING.md` | Contribution guidelines and governance |
| `docs/architecture/overview.md` | Architecture deep-dive |
| `docs/guides/getting-started.md` | Setup instructions |
| `docs/guides/testing.md` | Test suite documentation |
| `docs/api/endpoints.md` | API reference |
| `docs/CONVENTIONS.md` | Coding patterns and conventions |

---

## 🐛 Known Bugs Catalogue

> **These bugs are INTENTIONAL. They exist for educational and demonstration purposes. Do NOT fix them unless the user explicitly requests a fix.**

### 1. SQL Injection Vulnerability

- **File:** `src/main.py`, **line 153**
- **Function:** `delete_task()`
- **Bug:** Uses an f-string to interpolate `task_id` directly into a SQL query instead of a parameterized query.
- **Vulnerable code:**
  ```python
  query = f"DELETE FROM tasks WHERE id = {task_id}"
  ```
- **Safe alternative:**
  ```python
  conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
  ```

### 2. Memory Leaks — Unclosed Database Connections

- **File:** `src/main.py`, **lines 42, 68, 81, 104, 139, 157, 174**
- **Bug:** Every function that calls `get_db_connection()` (line 22) creates a new `sqlite3` connection but **never closes it**. Connections accumulate without cleanup.
- **Affected functions:**
  - `init_db()` — leak at line 42
  - `list_tasks()` — leak at line 68
  - `get_task()` — leak at line 81
  - `create_task()` — leak at line 104
  - `update_task()` — leak at line 139
  - `delete_task()` — leak at line 157
  - `complete_task()` — leak at line 174

### 3. Missing Input Validation — Empty Titles Accepted

- **File:** `src/main.py`, **line 86**
- **Function:** `create_task()`
- **Bug:** The endpoint signature `async def create_task(title: str, description: str = "")` accepts any string, including empty strings, as a title. There is no validation to reject empty or whitespace-only titles.

### 4. Missing 404 Handling — Crashes on Nonexistent Task IDs

- **File:** `src/main.py`, **lines 78, 137, 171**
- **Functions:** `get_task()`, `update_task()`, `complete_task()`
- **Bug:** `fetchone()` results are never null-checked. When a nonexistent task ID is requested, `dict(task)` is called on `None`, causing an unhandled `TypeError` instead of returning an HTTP 404 response.
  - `get_task()` — fetchone at line 78, missing check before line 82
  - `update_task()` — fetchone at line 137, missing check before line 140
  - `complete_task()` — fetchone at line 171, missing check before line 175

### 5. Code Duplication

- **File:** `src/main.py` (throughout)
- **Bug:** Repeated boilerplate pattern across all endpoints:
  ```python
  conn = get_db_connection()
  conn.execute(...)
  # ... no close
  return dict(task)
  ```
- No shared helper or context manager is used for connection lifecycle or row-to-dict conversion.

### 6. Hard-coded Configuration

- **File:** `src/main.py`
- **Locations:**
  - **Line 19:** `DATABASE_PATH = "tasks.db"` — database file path is a module-level constant
  - **Line 181:** `uvicorn.run(app, host="0.0.0.0", port=8000)` — host and port are hard-coded
- **Impact:** No environment-based configuration; cannot change settings without editing source code.

### 7. Failing Tests — Commented-Out Client Fixture

- **File:** `test/test_tasks.py`, **lines 22–24**
- **Bug:** The `client` pytest fixture is commented out:
  ```python
  # @pytest.fixture
  # def client():
  #     return TestClient(app)
  ```
- **Impact:** Every test function accepts a `client` parameter, but no fixture provides it, so **all tests fail** with a fixture-not-found error.

---

## Architectural Decisions & Gotchas

### Query Parameter Endpoints (Not JSON Body)
`POST /tasks` and `PUT /tasks/{task_id}` accept input as **query parameters**, not JSON request bodies. For example:
```
POST /tasks?title=My+Task&description=Details
```
This is deliberate — there are **no Pydantic request models**.

### Direct sqlite3 Usage
The project uses Python's built-in `sqlite3` module directly — **no ORM** (no SQLAlchemy, no Tortoise). All SQL is handwritten.

### sqlite3.Row Factory
`conn.row_factory = sqlite3.Row` (line 25) enables dict-like access on query results, which is why `dict(task)` works to convert rows to JSON-serializable dicts.

### Single-File Architecture
All application code lives in `src/main.py` **by design**. This is not a refactoring oversight — it is intentional to keep the sandbox simple and self-contained.

### No Migrations
The database schema is created on startup via `init_db()` with `CREATE TABLE IF NOT EXISTS`. There is no migration system.

---

## Documentation Map

| Document | Description |
|----------|-------------|
| [README.md](../README.md) | Project overview and quick reference |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guidelines and governance |
| [mcp.md](../mcp.md) | MCP governance policy |
| [docs/architecture/overview.md](../docs/architecture/overview.md) | Architecture deep-dive |
| [docs/guides/getting-started.md](../docs/guides/getting-started.md) | Getting started guide |
| [docs/guides/testing.md](../docs/guides/testing.md) | Testing guide |
| [docs/api/endpoints.md](../docs/api/endpoints.md) | API endpoint reference |
| [docs/CONVENTIONS.md](../docs/CONVENTIONS.md) | Coding conventions and patterns |

---

## Quick Reference for AI Agents

1. **Start here** — Read this file first for full project context.
2. **Source code** — `src/main.py` is the only application file.
3. **Tests** — `test/test_tasks.py` — all tests currently fail due to the commented-out fixture.
4. **Do not auto-fix bugs** — All bugs listed above are intentional unless the user says otherwise.
5. **Endpoints use query params** — Not JSON bodies. Adjust HTTP requests accordingly.
6. **No ORM** — Raw SQL via `sqlite3`. Understand the `sqlite3.Row` factory pattern.
