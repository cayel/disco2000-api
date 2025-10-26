import os


import pytest

from httpx import AsyncClient
from httpx import ASGITransport
from main import app

@pytest.mark.asyncio
async def test_get_artists_list(monkeypatch):
    class DummyArtist:
        def __init__(self, id, name, discogs_id):
            self.id = id
            self.name = name
            self.discogs_id = discogs_id
    class DummyResult:
        def scalars(self):
            class DummyScalar:
                def all(self_inner):
                    return [DummyArtist(1, "Artist 1", 123), DummyArtist(2, "Artist 2", 456)]
            return DummyScalar()
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def execute(self, stmt):
            return DummyResult()
    import main
    monkeypatch.setattr(main, "SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/artists", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for artist in data:
            assert isinstance(artist, dict)
            assert "id" in artist
            assert "name" in artist
            assert "discogs_id" in artist
