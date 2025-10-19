
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_get_albums_structure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/albums")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for album in data:
            assert isinstance(album, dict)
            assert "artist" in album
            assert "title" in album
            assert "year" in album
            assert "cover_url" in album
