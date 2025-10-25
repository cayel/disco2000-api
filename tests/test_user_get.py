import os
import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

@pytest.mark.asyncio
async def test_list_users(monkeypatch):
    # Patch SessionLocal pour simuler la base
    class DummyUser:
        def __init__(self, id, first_name, last_name, email, identifier, roles):
            self.id = id
            self.first_name = first_name
            self.last_name = last_name
            self.email = email
            self.identifier = identifier
            self.roles = roles
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def execute(self, *args, **kwargs):
            class DummyRes:
                def scalars(self):
                    class DummyAll:
                        def all(self):
                            return [
                                DummyUser(1, "Alice", "Martin", "alice@example.com", "alice01", ["utilisateur"]),
                                DummyUser(2, "Bob", "Dupont", "bob@example.com", "bob01", ["contributeur", "administrateur"])
                            ]
                    return DummyAll()
            return DummyRes()
    monkeypatch.setattr("user_endpoints.SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["first_name"] == "Alice"
        assert data[1]["roles"] == ["contributeur", "administrateur"]
