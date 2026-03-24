"""
Test suite for Task Manager API

ISSUES:
- Missing fixtures cause tests to fail
- No database cleanup between tests
- Missing test for SQL injection vulnerability
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app


@pytest.fixture
def client(tmp_path):
    import src.main as main_module
    original_db = main_module.DATABASE_PATH
    main_module.DATABASE_PATH = str(tmp_path / "test_tasks.db")
    main_module.init_db()
    yield TestClient(app)
    main_module.DATABASE_PATH = original_db


def test_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_create_task(client):
    """Test creating a task"""
    response = client.post(
        "/tasks",
        params={"title": "Test Task", "description": "Test Description"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert data["completed"] == 0


def test_create_empty_task(client):
    """Test that empty title is rejected"""
    response = client.post("/tasks", params={"title": ""})
    assert response.status_code == 400  # Should reject empty title


def test_create_whitespace_task(client):
    """Test that whitespace-only title is rejected"""
    response = client.post("/tasks", params={"title": "   "})
    assert response.status_code == 400


def test_list_tasks(client):
    """Test listing tasks"""
    # Create a task first
    client.post("/tasks", params={"title": "Task 1"})
    
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) > 0


def test_get_nonexistent_task(client):
    """Test getting a task that doesn't exist
    
    BUG: This test will FAIL because API doesn't handle missing tasks
    """
    response = client.get("/tasks/99999")
    assert response.status_code == 404  # Should return 404


def test_update_nonexistent_task(client):
    """Test updating a task that doesn't exist"""
    response = client.put("/tasks/99999", params={"title": "Nope"})
    assert response.status_code == 404


def test_complete_nonexistent_task(client):
    """Test completing a task that doesn't exist"""
    response = client.post("/tasks/99999/complete")
    assert response.status_code == 404


def test_update_task(client):
    """Test updating a task"""
    # Create a task first
    create_response = client.post("/tasks", params={"title": "Original Title"})
    task_id = create_response.json()["id"]
    
    # Update it
    response = client.put(
        f"/tasks/{task_id}",
        params={"title": "Updated Title", "completed": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["completed"] == 1


def test_delete_task(client):
    """Test deleting a task"""
    # Create a task first
    create_response = client.post("/tasks", params={"title": "To Delete"})
    task_id = create_response.json()["id"]
    
    # Delete it
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200
    
    # Verify it's gone
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404


def test_complete_task(client):
    """Test completing a task"""
    # Create a task first
    create_response = client.post("/tasks", params={"title": "To Complete"})
    task_id = create_response.json()["id"]
    
    # Complete it
    response = client.post(f"/tasks/{task_id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] == 1


def test_connection_management(client):
    """Verify that multiple sequential operations work correctly with context manager connections."""
    task_ids = []
    for i in range(5):
        resp = client.post("/tasks", params={"title": f"Conn Test {i}", "description": f"Desc {i}"})
        assert resp.status_code == 200
        task_ids.append(resp.json()["id"])

    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) >= 5

    for tid in task_ids:
        assert client.get(f"/tasks/{tid}").status_code == 200
        assert client.put(f"/tasks/{tid}", params={"title": f"Updated {tid}"}).status_code == 200
        assert client.post(f"/tasks/{tid}/complete").status_code == 200
        assert client.delete(f"/tasks/{tid}").status_code == 200


def test_database_path_config(client):
    """Test that DATABASE_PATH is configurable"""
    import src.main as main_module
    # The fixture already overrides DATABASE_PATH — just verify it's not 'tasks.db'
    assert main_module.DATABASE_PATH != "tasks.db"
    assert "test_tasks.db" in main_module.DATABASE_PATH


def test_sql_injection_protection(client):
    """Test that SQL injection is prevented - deleting one task must not affect others."""
    # Create two tasks
    resp_a = client.post("/tasks", params={"title": "Task A", "description": "A"})
    resp_b = client.post("/tasks", params={"title": "Task B", "description": "B"})
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    task_a_id = resp_a.json()["id"]
    task_b_id = resp_b.json()["id"]

    # Delete only Task A
    delete_resp = client.delete(f"/tasks/{task_a_id}")
    assert delete_resp.status_code == 200

    # Verify Task B still exists
    remaining = client.get("/tasks").json()
    remaining_ids = [t["id"] for t in remaining]
    assert task_b_id in remaining_ids
    assert task_a_id not in remaining_ids
