from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.routes.vectors import router as vectors_router

app = FastAPI()
app.include_router(vectors_router)

client = TestClient(app)

def test_upload_vector():
    response = client.post("/vectors/upload", json={"vector": [0.1, 0.2, 0.3], "metadata": {"doc_id": "123"}})
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["status"] == "success"

def test_retrieve_vector():
    response = client.get("/vectors/retrieve/123")
    assert response.status_code == 200
    assert response.json()["id"] == "123"

def test_delete_vector():
    response = client.delete("/vectors/delete/123")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"