def make_album():
    a = Album()
    a.id = 77
    a.title = "Existing Album"
    a.discogs_master_id = 555
    a.year = 2010
    a.genre = "Rock"
    a.style = "Indie"
    a.cover_url = "http://img.com/existing.jpg"
    a.type = "Studio"
    a.artist_id = 42
    a.label_id = 1
    return a


import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient

from main import app
from models import Album

client = TestClient(app)
headers = {"X-API-KEY": os.getenv("API_KEY")}

def test_add_studio_album_error(monkeypatch):
    async def dummy_fetch_discogs_master(master_id):
        raise Exception("Erreur Discogs")
    monkeypatch.setattr("main.fetch_discogs_master", dummy_fetch_discogs_master)
    response = client.post("/api/albums/studio?master_id=999", headers=headers)
    assert response.status_code == 500

def test_add_studio_album_artist_exists(monkeypatch):
    """Teste que si l'artiste existe déjà, il n'est pas recréé et l'album est lié à l'artiste existant."""
    class DummyLabel:
        def __init__(self):
            self.name = "Test Label"
            self.id = 1
            self.catno = "TL001"
    class DummyMaster:
        artiste = "Existing Artist"
        titre = "Existing Album"
        identifiants_discogs = {"master_id": 321, "main_release": 654}
        genres = ["Rock"]
        styles = ["Indie"]
        annee = 2010
        label = [DummyLabel()]
        pochette = "http://img.com/existing.jpg"
    async def dummy_fetch_discogs_master(master_id):
        return DummyMaster()
    monkeypatch.setattr("main.fetch_discogs_master", dummy_fetch_discogs_master)
    # Simule un artiste existant
    class DummyArtist:
        def __init__(self):
            self.id = 42
            self.name = "Existing Artist"
    class DummyAlbum:
        def __init__(self):
            self.id = 1234
            self.title = "Some Album"
    class DummySession:
        def __init__(self):
            self.added = []
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def execute(self, stmt, *args, **kwargs):
            # Sélectionne sur Artist
            if "Artist" in str(stmt):
                class DummyRes:
                    def scalar_one_or_none(self):
                        return DummyArtist()  # L'artiste existe déjà
                return DummyRes()
            # Sélectionne sur Album
            if "Album" in str(stmt):
                class DummyRes:
                    def scalar_one_or_none(self):
                        return None  # Pas d'album existant
                return DummyRes()
            # Par défaut
            class DummyRes:
                def scalar_one_or_none(self):
                    return None
            return DummyRes()
        async def flush(self):
            pass
        async def commit(self):
            pass
        def add(self, obj):
            self.added.append(type(obj).__name__)
            obj.id = 99
    dummy_session = DummySession()
    monkeypatch.setattr("main.SessionLocal", lambda: dummy_session)
    response = client.post("/api/albums/studio?master_id=321", headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Album studio ajouté"
    assert data["album_id"] == 99
    # Vérifie qu'un album a bien été ajouté mais pas de doublon artiste
    assert dummy_session.added.count("Artist") == 1  # Un seul ajout d'artiste (l'existant)
    assert dummy_session.added.count("Album") == 1  # Un album ajouté

def test_add_studio_album_album_exists(monkeypatch):
    """Teste qu'on n'insère pas un album qui existe déjà dans la base."""
    class DummyLabel:
        def __init__(self):
            self.name = "Test Label"
            self.id = 1
            self.catno = "TL001"
    class DummyMaster:
        artiste = "Existing Artist"
        titre = "Existing Album"
        identifiants_discogs = {"master_id": 555, "main_release": 666}
        genres = ["Rock"]
        styles = ["Indie"]
        annee = 2010
        label = [DummyLabel()]
        pochette = "http://img.com/existing.jpg"
    async def dummy_fetch_discogs_master(master_id):
        return DummyMaster()
    monkeypatch.setattr("main.fetch_discogs_master", dummy_fetch_discogs_master)
    # Simule un album existant
    class DummySession:
        def __init__(self):
            self.added = []
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def execute(self, stmt, *args, **kwargs):
            print(f"MOCK SESSION EXECUTE: {stmt}")
            # Sélectionne sur Artist
            if "Artist" in str(stmt):
                class DummyRes:
                    def scalar_one_or_none(self):
                        class DummyArtist:
                            def __init__(self):
                                self.id = 42
                                self.name = "Existing Artist"
                        return DummyArtist()
                return DummyRes()
            # Patch le master Discogs pour renvoyer un master factice
            class DummyMaster:
                artiste = "Existing Artist"
                titre = "Existing Album"
                identifiants_discogs = {"master_id": 555, "main_release": 666}
                genres = ["Rock"]
                styles = ["Indie"]
                annee = 2010
                label = []
                pochette = "http://img.com/existing.jpg"
            async def dummy_fetch_discogs_master(master_id):
                return DummyMaster()
            import main
            monkeypatch.setattr(main, "fetch_discogs_master", dummy_fetch_discogs_master)
            # Patch la session pour renvoyer un album existant
            from models import Album, Artist
            class DummySession:
                def __init__(self):
                    self.added = []
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc, tb):
                    pass
                async def execute(self, stmt, *args, **kwargs):
                    if "Artist" in str(stmt):
                        class DummyRes:
                            def scalar_one_or_none(self):
                                return Artist(id=42, name="Existing Artist")
                        return DummyRes()
                    if "Album" in str(stmt):
                        class DummyRes:
                            def scalar_one_or_none(self):
                                return Album(id=77, title="Existing Album", discogs_master_id=555)
                        return DummyRes()
                    class DummyRes:
                        def scalar_one_or_none(self):
                            return None
                    return DummyRes()
                async def flush(self):
                    pass
                async def commit(self):
                    pass
                def add(self, obj):
                    self.added.append(type(obj).__name__)
                    obj.id = 99
            monkeypatch.setattr(main, "SessionLocal", lambda: DummySession())
            headers = {"X-API-KEY": "NousNavionsPasFiniDeNousParlerDAmour"}
            response = client.post("/api/albums/studio?master_id=555", headers=headers)
            assert response.status_code == 409
            data = response.json()
            assert "existe déjà" in data.get("detail", "") or "déjà" in data.get("detail", "")
