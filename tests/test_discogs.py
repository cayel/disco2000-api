
import sys
import os
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

client = TestClient(app)

def test_discogs_master_success(monkeypatch):
    """Teste la récupération d'un master avec réponse simulée Discogs."""
    # Patch httpx.AsyncClient.get pour retourner une réponse simulée
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json = json_data
            self.status_code = status_code
        def json(self):
            return self._json
    async def mock_get(self, url, headers=None):
        if "masters" in url:
            return MockResponse({
                "id": 123,
                "main_release": 456,
                "artists": [{"name": "Test Artist"}],
                "title": "Test Title",
                "genres": ["Electronic"],
                "styles": ["Techno"],
                "year": 2000,
                "labels": [{"name": "Test Label", "id": 1, "catno": "TL001"}],
                "images": [{"type": "primary", "uri": "http://img.com/cover.jpg"}]
            })
        if "releases" in url:
            return MockResponse({"labels": [{"name": "Fallback Label", "id": 2, "catno": "FB001"}]})
        return MockResponse({}, status_code=404)
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    headers = {"X-API-KEY": os.getenv("API_KEY")}
    response = client.get("/api/discogs/master/123", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["artiste"] == "Test Artist"
    assert data["titre"] == "Test Title"
    assert data["genres"] == ["Electronic"]
    assert data["styles"] == ["Techno"]
    assert data["annee"] == 2000
    assert data["label"][0]["name"] == "Test Label"
    assert data["label"][0]["id"] == 1
    assert data["label"][0]["catno"] == "TL001"
    assert data["pochette"] == "http://img.com/cover.jpg"

def test_discogs_master_not_found(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code=404):
            self._json = json_data
            self.status_code = status_code
        def json(self):
            return self._json
    async def mock_get(self, url, headers=None):
        return MockResponse({}, status_code=404)
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    headers = {"X-API-KEY": "NousNavionsPasFiniDeNousParlerDAmour"}
    response = client.get("/api/discogs/master/999999", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Master non trouvé sur Discogs"