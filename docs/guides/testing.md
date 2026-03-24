# Testing Guide

This guide documents the test suite, known failures, and the intentional missing-fixture bug.

## Test Location

- **Test file:** `test/test_tasks.py` (not `tests/` — note the directory name)
- **Framework:** pytest with FastAPI's `TestClient`
- **HTTP client:** httpx (required by `TestClient`)

## Running Tests

```bash
pytest test/
```

## The Missing Fixture Issue

**All 9 tests will fail** with the error:

```
ERRORS - fixture 'client' not found
```

### Root Cause

In `test/test_tasks.py`, lines 22–24, the `client` pytest fixture is **commented out**:

```python
# BUG: Missing fixture - tests will fail
# @pytest.fixture
# def client():
#     return TestClient(app)
```

Every test function requires a `client` parameter, which pytest resolves as a fixture. Since the fixture definition is commented out, pytest cannot inject it and all tests error before they even run.

### How to Fix

Uncomment the fixture (lines 22–24 in `test/test_tasks.py`):

```python
@pytest.fixture
def client():
    return TestClient(app)
```

> **Note:** This is an **intentional educational bug** — it demonstrates what happens when pytest fixtures are missing. Do not fix it unless you are working on the fixture-related task.

## Test Inventory

Once the fixture is restored, the 9 tests have the following expected outcomes:

| # | Test Function                  | What It Tests                              | Expected Result |
|---|--------------------------------|--------------------------------------------|-----------------|
| 1 | `test_root(client)`            | `GET /` returns 200 with `"message"` key   | ✅ Pass          |
| 2 | `test_create_task(client)`     | `POST /tasks` with title and description   | ✅ Pass          |
| 3 | `test_create_empty_task(client)` | `POST /tasks` with empty title returns 400 | ❌ Fail         |
| 4 | `test_list_tasks(client)`      | `GET /tasks` returns non-empty list        | ✅ Pass          |
| 5 | `test_get_nonexistent_task(client)` | `GET /tasks/99999` returns 404        | ❌ Fail          |
| 6 | `test_update_task(client)`     | `PUT /tasks/{id}` updates title and completed | ✅ Pass       |
| 7 | `test_delete_task(client)`     | `DELETE /tasks/{id}` then `GET` returns 404 | ❌ Fail         |
| 8 | `test_complete_task(client)`   | `POST /tasks/{id}/complete` sets completed=1 | ✅ Pass        |
| 9 | `test_sql_injection_protection(client)` | Placeholder — body is `pass`      | ✅ Pass          |

### Summary: 6 pass, 3 fail (after fixture is restored)

## Expected Failures Explained

### `test_create_empty_task` — Expects 400, Gets 200

The test sends `POST /tasks` with `title=""` and asserts a 400 status code. However, the API (`src/main.py`, line 86) accepts the `title` query parameter as a plain `str` with no validation, so an empty string is accepted and a task is created with an empty title.

**Bug location:** `src/main.py` line 86 — no empty-title validation.

### `test_get_nonexistent_task` — Expects 404, Gets 500

The test calls `GET /tasks/99999` and expects a 404 response. The API (`src/main.py`, lines 72–82) fetches the row and calls `dict(task)` without checking if `task` is `None`, causing an unhandled `TypeError`.

**Bug location:** `src/main.py` lines 80–82 — no null check before `dict(task)`.

### `test_delete_task` — Verify Step Expects 404, Gets 500

The delete itself succeeds (200). But the verification step calls `GET /tasks/{id}` on the deleted task and asserts 404. This hits the same missing-error-handling bug as `test_get_nonexistent_task` — the API crashes instead of returning 404.

**Bug location:** Same as above — `src/main.py` lines 80–82.

## Test Details

### How Tests Send Data

All API endpoints accept **query parameters** (not JSON body). The tests use `params=` in their requests:

```python
client.post("/tasks", params={"title": "Test Task", "description": "Test Description"})
```

### No Database Cleanup

There is no teardown between tests. Each test that creates data leaves it in the database. The `tasks.db` file from the test run may accumulate rows across test sessions. This is a known limitation documented in the test file header.

## Adding New Tests

1. Add test functions to `test/test_tasks.py`
2. Use the `client` fixture parameter (once uncommented)
3. Follow the existing pattern — create data, then assert
4. Run with: `pytest test/ -v` for verbose output
