import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

@pytest.mark.asyncio
async def test_create_user_success(monkeypatch):
    # Patch SessionLocal pour simuler la base
    class DummyUser:
        def __init__(self, **kwargs):
            self.id = 1
            for k, v in kwargs.items():
                setattr(self, k, v)
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def execute(self, *args, **kwargs):
            class DummyRes:
                def scalar_one_or_none(self):
                    return None
            return DummyRes()
        def add(self, obj):
            self.obj = obj
        async def commit(self):
            pass
        async def refresh(self, obj):
            obj.id = 1
    monkeypatch.setattr("user_endpoints.SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "first_name": "Alice",
            "last_name": "Martin",
            "email": "alice@example.com",
            "identifier": "alice01",
            "roles": ["utilisateur", "contributeur"]
        }
        response = await client.post("/api/users", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Martin"
        assert data["email"] == "alice@example.com"
        assert data["identifier"] == "alice01"
        assert set(data["roles"]) == {"utilisateur", "contributeur"}

@pytest.mark.asyncio
async def test_create_user_conflict(monkeypatch):
    class DummyUser:
        pass
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def execute(self, *args, **kwargs):
            class DummyRes:
                def scalar_one_or_none(self):
                    return DummyUser()
            return DummyRes()
    monkeypatch.setattr("user_endpoints.SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "first_name": "Bob",
            "last_name": "Dupont",
            "email": "bob@example.com",
            "identifier": "bob01",
            "roles": ["administrateur"]
        }
        response = await client.post("/api/users", json=payload)
        assert response.status_code == 409
        assert response.json()["detail"] == "Email ou identifiant déjà utilisé"
