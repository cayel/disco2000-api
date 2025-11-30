"""
Tests pour l'endpoint de recherche d'artistes.
"""
import os
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


class DummyArtist:
    """Classe simulée pour représenter un artiste dans les tests."""
    def __init__(self, id, name, discogs_id, country):
        self.id = id
        self.name = name
        self.discogs_id = discogs_id
        self.country = country


def create_dummy_session(artists_list):
    """Factory pour créer une session simulée qui retourne une liste d'artistes spécifique."""
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
                            return artists_list
                    return DummyScalar()
            return DummyResult()
    return DummySession


@pytest.mark.asyncio
async def test_search_artists_exact_match(monkeypatch):
    """Test de recherche avec correspondance exacte."""
    artists = [DummyArtist(1, "The Beatles", 82730, "GB")]
    
    import artist_endpoints
    monkeypatch.setattr(artist_endpoints, "SessionLocal", lambda: create_dummy_session(artists)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/artists/search?q=Beatles", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["name"] == "The Beatles"
        assert data[0]["country"] == "GB"
        assert data[0]["country_name"] == "Royaume-Uni"


@pytest.mark.asyncio
async def test_search_artists_partial_match(monkeypatch):
    """Test de recherche avec correspondance partielle."""
    artists = [DummyArtist(1, "Pink Floyd", 45467, "GB")]
    
    import artist_endpoints
    monkeypatch.setattr(artist_endpoints, "SessionLocal", lambda: create_dummy_session(artists)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/artists/search?q=pink", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["name"] == "Pink Floyd"


@pytest.mark.asyncio
async def test_search_artists_case_insensitive(monkeypatch):
    """Test que la recherche est insensible à la casse."""
    artists = [DummyArtist(1, "Daft Punk", 1234, "FR")]
    
    import artist_endpoints
    monkeypatch.setattr(artist_endpoints, "SessionLocal", lambda: create_dummy_session(artists)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        # Test avec différentes casses
        response = await client.get("/api/artists/search?q=daft", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Daft Punk"


@pytest.mark.asyncio
async def test_search_artists_multiple_results(monkeypatch):
    """Test de recherche retournant plusieurs résultats."""
    artists = [
        DummyArtist(1, "Pink Floyd", 45467, "GB"),
        DummyArtist(2, "Pink", 1234, "US"),
        DummyArtist(3, "The Pink Spiders", 5678, "US")
    ]
    
    import artist_endpoints
    monkeypatch.setattr(artist_endpoints, "SessionLocal", lambda: create_dummy_session(artists)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/artists/search?q=pink", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        names = [a["name"] for a in data]
        assert "Pink Floyd" in names
        assert "Pink" in names
        assert "The Pink Spiders" in names


@pytest.mark.asyncio
async def test_search_artists_no_results(monkeypatch):
    """Test de recherche sans résultats."""
    artists = []
    
    import artist_endpoints
    monkeypatch.setattr(artist_endpoints, "SessionLocal", lambda: create_dummy_session(artists)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/artists/search?q=zzzzz", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 0
        assert data == []


@pytest.mark.asyncio
async def test_search_artists_with_special_characters(monkeypatch):
    """Test de recherche avec caractères spéciaux."""
    artists = [DummyArtist(1, "AC/DC", 1234, "AU")]
    
    import artist_endpoints
    monkeypatch.setattr(artist_endpoints, "SessionLocal", lambda: create_dummy_session(artists)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/artists/search?q=AC/DC", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["name"] == "AC/DC"


@pytest.mark.asyncio
async def test_search_artists_missing_query_param():
    """Test que le paramètre q est obligatoire."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/artists/search", headers=headers)
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_search_artists_includes_country_info(monkeypatch):
    """Test que les informations de pays sont incluses dans les résultats."""
    artists = [
        DummyArtist(1, "Daft Punk", 1234, "FR"),
        DummyArtist(2, "Justice", 5678, None)
    ]
    
    import artist_endpoints
    monkeypatch.setattr(artist_endpoints, "SessionLocal", lambda: create_dummy_session([artists[0]])())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        # Recherche Daft Punk (avec pays)
        response = await client.get("/api/artists/search?q=daft", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["country"] == "FR"
        assert data[0]["country_name"] == "France"


@pytest.mark.asyncio
async def test_search_artists_without_country(monkeypatch):
    """Test pour un artiste sans pays."""
    artists = [DummyArtist(1, "Justice", 5678, None)]
    
    import artist_endpoints
    monkeypatch.setattr(artist_endpoints, "SessionLocal", lambda: create_dummy_session(artists)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/artists/search?q=justice", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["country"] is None
        assert data[0]["country_name"] is None


@pytest.mark.asyncio
async def test_search_artists_response_structure(monkeypatch):
    """Test de la structure de la réponse."""
    artists = [DummyArtist(1, "Test Artist", 9999, "US")]
    
    import artist_endpoints
    monkeypatch.setattr(artist_endpoints, "SessionLocal", lambda: create_dummy_session(artists)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/artists/search?q=test", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 1
        
        artist = data[0]
        assert "id" in artist
        assert "name" in artist
        assert "discogs_id" in artist
        assert "country" in artist
        assert "country_name" in artist
        
        assert artist["id"] == 1
        assert artist["name"] == "Test Artist"
        assert artist["discogs_id"] == 9999
        assert artist["country"] == "US"
        assert artist["country_name"] == "États-Unis"
