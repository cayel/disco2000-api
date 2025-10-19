

import pytest

from httpx import AsyncClient
from httpx import ASGITransport
from main import app

@pytest.mark.asyncio
async def test_get_artists_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/artists")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Vérifie que chaque élément est un dict avec les bonnes clés
        for artist in data:
            assert isinstance(artist, dict)
            assert "id" in artist
            assert "name" in artist
            assert "discogs_id" in artist
