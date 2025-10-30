import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_vector_service_upload():
    response = client.post(
        "/api/v1/vector/upload",
        json={"file_name": "test_file.pdf", "database_name": "test_db"}
    )
    assert response.status_code == 200
    assert "file_name" in response.json()
    assert "unique_id" in response.json()
    assert "upload_status" in response.json()
    assert response.json()["file_name"] == "test_file.pdf"
    assert response.json()["upload_status"] == "success"

def test_vector_service_delete():
    response = client.delete(
        "/api/v1/vector/delete",
        json={"unique_id": "some_unique_id"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

def test_vector_service_recall():
    response = client.post(
        "/api/v1/vector/recall",
        json={"query_vector": [0.1, 0.2, 0.3]}
    )
    assert response.status_code == 200
    assert "results" in response.json()