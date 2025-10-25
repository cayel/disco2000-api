import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

class DummyIdInfo:
    def __init__(self, email, given_name, family_name):
        self.email = email
        self.given_name = given_name
        self.family_name = family_name
    def get(self, key, default=None):
        return getattr(self, key, default)
    def __getitem__(self, key):
        return getattr(self, key)

@pytest.mark.asyncio
async def test_get_user_token_google_success(monkeypatch):
    # Patch Firebase token verification
    def fake_verify_id_token(id_token):
        return {
            "email": "alice@example.com",
            "given_name": "Alice",
            "family_name": "Martin"
        }
    monkeypatch.setattr(
        "firebase_admin.auth.verify_id_token",
        fake_verify_id_token
    )
    transport = ASGITransport(app=app)
    api_key = os.getenv("API_KEY")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": api_key}
        response = await client.post(
            "/api/users/token",
            json={"id_token": "fake-google-token"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_user_token_google_invalid(monkeypatch):
    def fake_verify_id_token(id_token):
        raise Exception("Invalid token")
    monkeypatch.setattr(
        "firebase_admin.auth.verify_id_token",
        fake_verify_id_token
    )
    transport = ASGITransport(app=app)
    api_key = os.getenv("API_KEY")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-API-KEY": api_key}
        response = await client.post(
            "/api/users/token",
            json={"id_token": "bad-token"},
            headers=headers
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Token Google invalide"
