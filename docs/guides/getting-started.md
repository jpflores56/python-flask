# Getting Started

This guide walks you through setting up and running the Task Manager API locally.

## Prerequisites

- **Python 3.8+** — verify with `python --version`
- **pip** — Python package manager (included with Python)

## Setup

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd python-flask-main
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package   | Version  | Purpose                        |
|-----------|----------|--------------------------------|
| fastapi   | 0.104.1  | Web framework for the API      |
| uvicorn   | 0.24.0   | ASGI server to run FastAPI     |
| pytest    | 7.4.3    | Test framework                 |
| httpx     | 0.25.1   | HTTP client (used by tests)    |

### 3. Run the API

```bash
python src/main.py
```

The server starts on **http://0.0.0.0:8000** via uvicorn.

### 4. Database Initialization

No manual setup is required. On startup, `init_db()` automatically creates a `tasks.db` SQLite file in the project root with the `tasks` table.

### 5. Verify It Works

```bash
curl http://localhost:8000/
```

Expected response:

```json
{"message": "Task Manager API", "version": "1.0.0"}
```

## API Endpoints

| Method | Path                       | Description              |
|--------|----------------------------|--------------------------|
| GET    | `/`                        | Health check             |
| GET    | `/tasks`                   | List all tasks           |
| GET    | `/tasks/{id}`              | Get a single task        |
| POST   | `/tasks`                   | Create a task            |
| PUT    | `/tasks/{id}`              | Update a task            |
| DELETE | `/tasks/{id}`              | Delete a task            |
| POST   | `/tasks/{id}/complete`     | Mark a task as completed |

> **Note:** POST, PUT, and DELETE endpoints accept parameters as **query parameters**, not JSON body.

### Example: Create a Task

```bash
curl -X POST "http://localhost:8000/tasks?title=My+Task&description=A+sample+task"
```

## Running Tests

```bash
pytest test/
```

> **Note:** Some tests will fail intentionally due to known issues in the codebase. See the [Testing Guide](testing.md) for details.

## Project Structure

```
python-flask-main/
├── src/
│   └── main.py            # FastAPI application and all endpoints
├── test/
│   ├── __init__.py
│   └── test_tasks.py      # Test suite (9 tests)
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── README.md
```

## Troubleshooting

- **Port 8000 in use:** Kill the existing process or change the port in `src/main.py` (line 181).
- **Module not found errors:** Ensure you run `pip install -r requirements.txt` from the project root.
- **Database issues:** Delete `tasks.db` and restart the server — it will be recreated automatically.
