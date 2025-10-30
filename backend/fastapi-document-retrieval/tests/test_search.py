from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_search_documents():
    response = client.get("/search", params={"query": "example"})
    assert response.status_code == 200
    assert "results" in response.json()

def test_search_no_results():
    response = client.get("/search", params={"query": "nonexistent"})
    assert response.status_code == 200
    assert response.json() == {"results": []}

def test_search_invalid_query():
    response = client.get("/search", params={"query": ""})
    assert response.status_code == 400
    assert "detail" in response.json()