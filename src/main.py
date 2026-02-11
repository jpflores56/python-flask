"""
Task Management API - Main application file

KNOWN ISSUES (for demonstration):
- SQL injection vulnerability in delete_task
- No validation for empty task titles
- Duplicate code in CRUD operations
- Missing error handling
"""

from fastapi import FastAPI, HTTPException
from typing import List, Optional
import sqlite3
from datetime import datetime

app = FastAPI(title="Task Manager API")

# Hard-coded configuration (BAD PRACTICE - should be in config file)
DATABASE_PATH = "tasks.db"


def get_db_connection():
    """Get database connection - WARNING: Not properly closed (memory leak)"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with tasks table"""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    # BUG: Connection never closed - memory leak!


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def root():
    return {"message": "Task Manager API", "version": "1.0.0"}


@app.get("/tasks", response_model=List[dict])
async def list_tasks(completed: Optional[bool] = None):
    """List all tasks, optionally filter by completion status"""
    conn = get_db_connection()
    
    # DUPLICATE CODE - Same pattern used in multiple endpoints
    if completed is None:
        query = "SELECT * FROM tasks ORDER BY created_at DESC"
        tasks = conn.execute(query).fetchall()
    else:
        query = "SELECT * FROM tasks WHERE completed = ? ORDER BY created_at DESC"
        tasks = conn.execute(query, (1 if completed else 0,)).fetchall()
    
    # BUG: Connection never closed
    return [dict(task) for task in tasks]


@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    """Get a single task by ID"""
    conn = get_db_connection()
    
    # DUPLICATE CODE - Same pattern as above
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    
    # MISSING ERROR HANDLING - What if task doesn't exist?
    # BUG: Connection never closed
    return dict(task)


@app.post("/tasks")
async def create_task(title: str, description: str = ""):
    """Create a new task
    
    BUG: No validation for empty title
    """
    conn = get_db_connection()
    
    # DUPLICATE CODE - Same insert pattern
    cursor = conn.execute(
        "INSERT INTO tasks (title, description) VALUES (?, ?)",
        (title, description)
    )
    conn.commit()
    task_id = cursor.lastrowid
    
    # DUPLICATE CODE - Same fetch pattern
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    
    # BUG: Connection never closed
    return dict(task)


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, title: str = None, description: str = None, completed: bool = None):
    """Update a task"""
    conn = get_db_connection()
    
    # MISSING ERROR HANDLING - What if task doesn't exist?
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if completed is not None:
        updates.append("completed = ?")
        params.append(1 if completed else 0)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    params.append(task_id)
    query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
    
    conn.execute(query, params)
    conn.commit()
    
    # DUPLICATE CODE - Same fetch pattern
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    
    # BUG: Connection never closed
    return dict(task)


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task
    
    CRITICAL BUG: SQL injection vulnerability!
    """
    conn = get_db_connection()
    
    # SECURITY VULNERABILITY - SQL Injection!
    # Should use parameterized query like: "DELETE FROM tasks WHERE id = ?", (task_id,)
    query = f"DELETE FROM tasks WHERE id = {task_id}"
    conn.execute(query)
    conn.commit()
    
    # BUG: Connection never closed
    return {"message": "Task deleted successfully"}


@app.post("/tasks/{task_id}/complete")
async def complete_task(task_id: int):
    """Mark a task as completed"""
    conn = get_db_connection()
    
    # DUPLICATE CODE - Same update pattern
    conn.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
    conn.commit()
    
    # DUPLICATE CODE - Same fetch pattern
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    
    # MISSING ERROR HANDLING
    # BUG: Connection never closed
    return dict(task)


if __name__ == "__main__":
    import uvicorn
    # Hard-coded port (should be in config)
    uvicorn.run(app, host="0.0.0.0", port=8000)
