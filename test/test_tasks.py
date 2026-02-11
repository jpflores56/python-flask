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


# BUG: Missing fixture - tests will fail
# @pytest.fixture
# def client():
#     return TestClient(app)


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
    """Test that empty title is rejected
    
    BUG: This test will FAIL because API doesn't validate empty titles
    """
    response = client.post("/tasks", params={"title": ""})
    assert response.status_code == 400  # Should reject empty title


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


# MISSING TEST: SQL injection vulnerability
def test_sql_injection_protection(client):
    """Test that SQL injection is prevented
    
    TODO: Add test for SQL injection in delete endpoint
    """
    pass
