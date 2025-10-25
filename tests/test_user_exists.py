import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

@pytest.mark.asyncio
async def test_user_exists_true(monkeypatch):
    class DummyUser:
        def __init__(self, email):
            self.email = email
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def execute(self, *args, **kwargs):
            class DummyRes:
                def scalar_one_or_none(self):
                    return DummyUser("alice@example.com")
            return DummyRes()
    monkeypatch.setattr("user_endpoints.SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": "NousNavionsPasFiniDeNousParlerDAmour"}
        response = await client.get("/api/users/exists", params={"email": "alice@example.com"}, headers=headers)
        assert response.status_code == 200
        assert response.json() == {"exists": True}

@pytest.mark.asyncio
async def test_user_exists_false(monkeypatch):
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
    monkeypatch.setattr("user_endpoints.SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": "NousNavionsPasFiniDeNousParlerDAmour"}
        response = await client.get("/api/users/exists", params={"email": "bob@example.com"}, headers=headers)
        assert response.status_code == 200
        assert response.json() == {"exists": False}
