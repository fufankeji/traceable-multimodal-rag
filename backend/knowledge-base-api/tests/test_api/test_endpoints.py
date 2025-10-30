from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_upload_file():
    response = client.post("/api/v1/files/upload", json={"filename": "test_file.txt", "data": "sample data"})
    assert response.status_code == 200
    assert "file_id" in response.json()
    assert response.json()["status"] == "uploaded"

def test_get_file_info():
    response = client.get("/api/v1/files/test_file.txt")
    assert response.status_code == 200
    assert response.json()["filename"] == "test_file.txt"

def test_delete_file():
    response = client.delete("/api/v1/files/test_file.txt")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

def test_create_knowledge_base():
    response = client.post("/api/v1/knowledge_base", json={"name": "Test Knowledge Base"})
    assert response.status_code == 200
    assert "knowledge_base_id" in response.json()
    assert response.json()["status"] == "created"

def test_search_chunks():
    response = client.post("/api/v1/search", json={"query": "sample query"})
    assert response.status_code == 200
    assert isinstance(response.json()["results"], list)