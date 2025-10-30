from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.routes.documents import router as documents_router
from src.api.routes.search import router as search_router
from src.api.routes.vectors import router as vectors_router

app = FastAPI()

app.include_router(documents_router)
app.include_router(search_router)
app.include_router(vectors_router)

client = TestClient(app)

def test_upload_document():
    response = client.post("/documents/upload", json={"file": "test.pdf", "db_name": "test_db"})
    assert response.status_code == 200
    assert "filename" in response.json()
    assert "id" in response.json()
    assert response.json()["status"] == "success"

def test_search_document():
    response = client.get("/search", params={"query": "test"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_upload_vector():
    response = client.post("/vectors/upload", json={"vector": [0.1, 0.2, 0.3], "doc_id": "123"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"