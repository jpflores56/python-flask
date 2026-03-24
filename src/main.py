"""
Task Management API - Main application file

KNOWN ISSUES (for demonstration):
- SQL injection vulnerability in delete_task
- No validation for empty task titles
- Duplicate code in CRUD operations
- Missing error handling
"""

import os
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException
from typing import List, Optional
import sqlite3
from datetime import datetime

app = FastAPI(title="Task Manager API")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "tasks.db")


@contextmanager
def get_db_connection():
    """Get database connection with automatic cleanup"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database with tasks table"""
    with get_db_connection() as conn:
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


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def root():
    return {"message": "Task Manager API", "version": "1.0.0"}


@app.get("/tasks", response_model=List[dict])
async def list_tasks(completed: Optional[bool] = None):
    """List all tasks, optionally filter by completion status"""
    with get_db_connection() as conn:
        # DUPLICATE CODE - Same pattern used in multiple endpoints
        if completed is None:
            query = "SELECT * FROM tasks ORDER BY created_at DESC"
            tasks = conn.execute(query).fetchall()
        else:
            query = "SELECT * FROM tasks WHERE completed = ? ORDER BY created_at DESC"
            tasks = conn.execute(query, (1 if completed else 0,)).fetchall()
        
        return [dict(task) for task in tasks]


@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    """Get a single task by ID"""
    with get_db_connection() as conn:
        # DUPLICATE CODE - Same pattern as above
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return dict(task)


@app.post("/tasks")
async def create_task(title: str, description: str = ""):
    """Create a new task"""
    if not title or not title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    with get_db_connection() as conn:
        # DUPLICATE CODE - Same insert pattern
        cursor = conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            (title, description)
        )
        conn.commit()
        task_id = cursor.lastrowid
        
        # DUPLICATE CODE - Same fetch pattern
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        
        return dict(task)


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, title: str = None, description: str = None, completed: bool = None):
    """Update a task"""
    with get_db_connection() as conn:
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
        
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return dict(task)


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task"""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        
        return {"message": "Task deleted successfully"}


@app.post("/tasks/{task_id}/complete")
async def complete_task(task_id: int):
    """Mark a task as completed"""
    with get_db_connection() as conn:
        # DUPLICATE CODE - Same update pattern
        conn.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
        conn.commit()
        
        # DUPLICATE CODE - Same fetch pattern
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return dict(task)


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
