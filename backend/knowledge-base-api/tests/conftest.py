import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(scope="module")
def test_client():
    client = TestClient(app)
    yield client

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # Setup code for database (e.g., create tables, insert test data)
    yield
    # Teardown code for database (e.g., drop tables)