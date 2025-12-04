"""
Tests pour les endpoints de statistiques publiques.
"""
import os
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


class DummyAlbum:
    """Classe simulée pour représenter un album dans les tests."""
    def __init__(self, id, genre, style, year=None):
        self.id = id
        self.genre = genre  # Liste de genres
        self.style = style  # Liste de styles
        self.year = year


def create_dummy_session_for_stats(albums_list):
    """Factory pour créer une session simulée pour les statistiques."""
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def execute(self, stmt):
            # Détermine le type de requête en fonction du statement
            stmt_str = str(stmt)
            
            # Requête de comptage avec func.count()
            if "count(" in stmt_str.lower() and "select_from(albums)" in stmt_str.lower():
                class CountResult:
                    def scalar(self):
                        return len(albums_list)
                return CountResult()
            # Requête pour genres ET styles (deux colonnes)
            elif "albums.genre" in stmt_str.lower() and "albums.style" in stmt_str.lower():
                class GenreStyleResult:
                    def all(self):
                        return [(a.genre, a.style) for a in albums_list]
                return GenreStyleResult()
            # Requête uniquement pour les genres
            elif "albums.genre" in stmt_str.lower():
                class GenreResult:
                    def scalars(self):
                        class GenreScalar:
                            def all(self):
                                return [a.genre for a in albums_list]
                        return GenreScalar()
                return GenreResult()
            # Requête uniquement pour les styles
            elif "albums.style" in stmt_str.lower():
                class StyleResult:
                    def scalars(self):
                        class StyleScalar:
                            def all(self):
                                return [a.style for a in albums_list]
                        return StyleScalar()
                return StyleResult()
            else:
                # Requête par défaut (comptage aussi)
                class DefaultResult:
                    def scalars(self):
                        class DefaultScalar:
                            def all(self):
                                return albums_list
                        return DefaultScalar()
                    def scalar(self):
                        return len(albums_list)
                    def one(self):
                        return (None, None)
                    def all(self):
                        return []
                return DefaultResult()
    return DummySession


@pytest.mark.asyncio
async def test_genres_styles_statistics_structure(monkeypatch):
    """Test de la structure de la réponse des statistiques genres/styles."""
    albums = [
        DummyAlbum(1, ["Rock"], ["Hard Rock"], 1980),
        DummyAlbum(2, ["Rock", "Pop"], ["Alternative Rock"], 1990),
        DummyAlbum(3, ["Electronic"], ["House", "Techno"], 2000)
    ]
    
    import statistics_endpoints
    monkeypatch.setattr(statistics_endpoints, "SessionLocal", lambda: create_dummy_session_for_stats(albums)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/statistics/genres-styles", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Vérifie la structure
        assert "total_albums" in data
        assert "total_genres" in data
        assert "total_styles" in data
        assert "genres" in data
        assert "styles" in data
        
        assert isinstance(data["genres"], list)
        assert isinstance(data["styles"], list)
        assert data["total_albums"] == 3


@pytest.mark.asyncio
async def test_genres_statistics_counting(monkeypatch):
    """Test du comptage des genres."""
    albums = [
        DummyAlbum(1, ["Rock"], [], 1980),
        DummyAlbum(2, ["Rock"], [], 1990),
        DummyAlbum(3, ["Pop"], [], 2000),
        DummyAlbum(4, ["Rock"], [], 2010)
    ]
    
    import statistics_endpoints
    monkeypatch.setattr(statistics_endpoints, "SessionLocal", lambda: create_dummy_session_for_stats(albums)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/statistics/genres", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "genres" in data
        
        genres = {g["name"]: g["count"] for g in data["genres"]}
        assert genres["Rock"] == 3
        assert genres["Pop"] == 1


@pytest.mark.asyncio
async def test_styles_statistics_counting(monkeypatch):
    """Test du comptage des styles."""
    albums = [
        DummyAlbum(1, [], ["Hard Rock"], 1980),
        DummyAlbum(2, [], ["Hard Rock", "Heavy Metal"], 1990),
        DummyAlbum(3, [], ["Punk"], 2000)
    ]
    
    import statistics_endpoints
    monkeypatch.setattr(statistics_endpoints, "SessionLocal", lambda: create_dummy_session_for_stats(albums)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/statistics/styles", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "styles" in data
        
        styles = {s["name"]: s["count"] for s in data["styles"]}
        assert styles["Hard Rock"] == 2
        assert styles["Heavy Metal"] == 1
        assert styles["Punk"] == 1


@pytest.mark.asyncio
async def test_genres_sorted_by_count(monkeypatch):
    """Test que les genres sont triés par nombre d'occurrences (décroissant)."""
    albums = [
        DummyAlbum(1, ["Rock"], [], 1980),
        DummyAlbum(2, ["Pop"], [], 1990),
        DummyAlbum(3, ["Rock"], [], 2000),
        DummyAlbum(4, ["Jazz"], [], 2010),
        DummyAlbum(5, ["Rock"], [], 2015),
        DummyAlbum(6, ["Pop"], [], 2020)
    ]
    
    import statistics_endpoints
    monkeypatch.setattr(statistics_endpoints, "SessionLocal", lambda: create_dummy_session_for_stats(albums)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/statistics/genres", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        genres = data["genres"]
        # Vérifie que c'est trié par count décroissant
        assert genres[0]["name"] == "Rock"
        assert genres[0]["count"] == 3
        assert genres[1]["name"] == "Pop"
        assert genres[1]["count"] == 2
        assert genres[2]["name"] == "Jazz"
        assert genres[2]["count"] == 1


@pytest.mark.asyncio
async def test_genres_styles_with_multiple_values_per_album(monkeypatch):
    """Test avec plusieurs genres et styles par album."""
    albums = [
        DummyAlbum(1, ["Rock", "Pop"], ["Hard Rock", "Pop Rock"], 1980),
        DummyAlbum(2, ["Rock"], ["Hard Rock"], 1990)
    ]
    
    import statistics_endpoints
    monkeypatch.setattr(statistics_endpoints, "SessionLocal", lambda: create_dummy_session_for_stats(albums)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/statistics/genres-styles", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        genres = {g["name"]: g["count"] for g in data["genres"]}
        styles = {s["name"]: s["count"] for s in data["styles"]}
        
        # Rock apparaît dans 2 albums
        assert genres["Rock"] == 2
        # Pop apparaît dans 1 album
        assert genres["Pop"] == 1
        # Hard Rock apparaît dans 2 albums
        assert styles["Hard Rock"] == 2
        # Pop Rock apparaît dans 1 album
        assert styles["Pop Rock"] == 1


@pytest.mark.asyncio
async def test_statistics_with_empty_genres_styles(monkeypatch):
    """Test avec des albums sans genres ni styles."""
    albums = [
        DummyAlbum(1, [], [], 1980),
        DummyAlbum(2, None, None, 1990),
        DummyAlbum(3, ["Rock"], ["Hard Rock"], 2000)
    ]
    
    import statistics_endpoints
    monkeypatch.setattr(statistics_endpoints, "SessionLocal", lambda: create_dummy_session_for_stats(albums)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/statistics/genres-styles", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_albums"] == 3
        assert data["total_genres"] == 1  # Seulement "Rock"
        assert data["total_styles"] == 1  # Seulement "Hard Rock"


@pytest.mark.asyncio
async def test_statistics_public_access():
    """Test que les endpoints de statistiques nécessitent une API key."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Teste SANS le header X-API-KEY
        # L'API key est requise globalement dans l'application
        response = await client.get("/api/statistics/genres-styles")
        # On s'attend à une erreur 422 (validation error) sans API key
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_genres_response_structure(monkeypatch):
    """Test de la structure détaillée de la réponse genres."""
    albums = [DummyAlbum(1, ["Rock"], [], 1980)]
    
    import statistics_endpoints
    monkeypatch.setattr(statistics_endpoints, "SessionLocal", lambda: create_dummy_session_for_stats(albums)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/statistics/genres", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "genres" in data
        assert isinstance(data["genres"], list)
        
        if len(data["genres"]) > 0:
            genre = data["genres"][0]
            assert "name" in genre
            assert "count" in genre
            assert isinstance(genre["name"], str)
            assert isinstance(genre["count"], int)


@pytest.mark.asyncio
async def test_styles_response_structure(monkeypatch):
    """Test de la structure détaillée de la réponse styles."""
    albums = [DummyAlbum(1, [], ["Hard Rock"], 1980)]
    
    import statistics_endpoints
    monkeypatch.setattr(statistics_endpoints, "SessionLocal", lambda: create_dummy_session_for_stats(albums)())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": os.getenv("API_KEY")}
        response = await client.get("/api/statistics/styles", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "styles" in data
        assert isinstance(data["styles"], list)
        
        if len(data["styles"]) > 0:
            style = data["styles"][0]
            assert "name" in style
            assert "count" in style
            assert isinstance(style["name"], str)
            assert isinstance(style["count"], int)
