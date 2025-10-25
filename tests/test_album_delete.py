import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_delete_album_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.delete("/api/albums/999999", headers=headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Album non trouvé"

@pytest.mark.asyncio
async def test_delete_album_success(monkeypatch):
    # Patch SessionLocal pour simuler la présence d'un album
    class DummyAlbum:
        id = 42
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, model, album_id):
            if album_id == 42:
                return DummyAlbum()
            return None
        async def delete(self, obj):
            self.deleted = obj
        async def commit(self):
            self.committed = True
    monkeypatch.setattr("main.SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.delete("/api/albums/42", headers=headers)
        assert response.status_code == 204
