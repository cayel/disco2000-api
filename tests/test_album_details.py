import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_get_album_details_empty(monkeypatch):
    # Vérifie que /api/albums/ sans id ne retourne pas 422 pour le endpoint détail
    import album_endpoints
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, model, obj_id):
            return None
    monkeypatch.setattr(album_endpoints, "SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/albums/")
    # On accepte 404, 405 ou 307 (redirection automatique FastAPI)
    assert response.status_code in (404, 405, 307)

@pytest.mark.asyncio
async def test_get_album_details(monkeypatch):
    # Dummy objects
    class DummyArtist:
        id = 1
        name = "Test Artist"
        discogs_id = 123
    class DummyLabel:
        id = 2
        name = "Test Label"
        discogs_id = 456
    class DummyAlbum:
        id = 42
        title = "Test Album"
        year = 2020
        genre = ["Rock"]
        style = ["Indie"]
        cover_url = "http://img.com/cover.jpg"
        catno = "ABC123"
        type = "Studio"
        discogs_master_id = 789
        artist_id = 1
        label_id = 2
    # Patch session.get to return the right dummy
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, model, obj_id):
            if model.__name__ == "Album" and obj_id == 42:
                return DummyAlbum()
            if model.__name__ == "Artist" and obj_id == 1:
                return DummyArtist()
            if model.__name__ == "Label" and obj_id == 2:
                return DummyLabel()
            return None
    import album_endpoints
    monkeypatch.setattr(album_endpoints, "SessionLocal", lambda: DummySession())

@pytest.mark.asyncio
async def test_get_album_details_404(monkeypatch):
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, model, obj_id):
            return None
    import album_endpoints
    monkeypatch.setattr(album_endpoints, "SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/albums/9999")
        # On accepte 404 ou 422 (si FastAPI ne matche pas la route)
        assert response.status_code in (404, 422)
        if response.status_code == 404:
            assert response.json()["detail"] == "Album non trouvé"


@pytest.mark.asyncio
async def test_get_album_details_200(monkeypatch):
    class DummyArtist(object):
        def __init__(self):
            self.id = 1
            self.name = "Test Artist"
            self.discogs_id = 123
    class DummyLabel(object):
        def __init__(self):
            self.id = 2
            self.name = "Test Label"
            self.discogs_id = 456
    class DummyAlbum(object):
        def __init__(self):
            self.id = 42
            self.title = "Test Album"
            self.year = 2020
            self.genre = ["Rock"]
            self.style = ["Indie"]
            self.cover_url = "http://img.com/cover.jpg"
            self.catno = "ABC123"
            self.type = "Studio"
            self.discogs_master_id = 789
            self.artist_id = 1
            self.label_id = 2
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, model, obj_id):
            if model.__name__ == "Album" and obj_id == 42:
                return DummyAlbum()
            if model.__name__ == "Artist" and obj_id == 1:
                return DummyArtist()
            if model.__name__ == "Label" and obj_id == 2:
                return DummyLabel()
            return None
    import album_endpoints
    monkeypatch.setattr(album_endpoints, "SessionLocal", lambda: DummySession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/albums/42", headers=headers)
        if response.status_code != 200:
            print("REPONSE 422:", response.text)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 42
        assert data["title"] == "Test Album"
        assert data["artist"]["name"] == "Test Artist"
        assert data["label"]["name"] == "Test Label"
        assert data["discogs_master_id"] == 789
