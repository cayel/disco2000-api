import os

import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_get_albums_structure(monkeypatch):
    class DummyAlbum:
        def __init__(self, artist_id, title, year, cover_url):
            self.artist_id = artist_id
            self.title = title
            self.year = year
            self.cover_url = cover_url
    class DummyArtist:
        def __init__(self, id, name):
            self.id = id
            self.name = name
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def execute(self, stmt):
            class DummyResult:
                def scalars(self_inner):
                    class DummyScalar:
                        def all(self_inner2):
                            return [DummyAlbum(1, "Album 1", 2020, "url1"), DummyAlbum(2, "Album 2", 2021, "url2")]
                    return DummyScalar()
            return DummyResult()
        async def get(self, model, obj_id):
            if model.__name__ == "Artist":
                return DummyArtist(obj_id, f"Artist {obj_id}")
            return None
    import album_endpoints
    monkeypatch.setattr(album_endpoints, "SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/albums", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for album in data:
            assert isinstance(album, dict)
            assert "artist" in album
            assert "title" in album
            assert "year" in album
            assert "cover_url" in album
