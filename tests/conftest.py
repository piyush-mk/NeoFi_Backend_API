import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture
def user_data():
    unique = str(uuid.uuid4())[:8]
    return {
        "email": f"testuser_{unique}@example.com",
        "username": f"testuser_{unique}",
        "password": "testpass"
    }

@pytest.fixture
def auth_headers(client, user_data):
    client.post("/api/auth/register", json=user_data)
    resp = client.post("/api/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"} 