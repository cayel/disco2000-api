
from fastapi import Header, Depends
from dotenv import load_dotenv
load_dotenv()
import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi import Path
from user_endpoints import router as user_router

import httpx
from pydantic import BaseModel, Field

# ... autres imports ...

class LabelInfo(BaseModel):
    name: str
    id: Optional[int] = None
    catno: Optional[str] = None

class DiscogsMasterResponse(BaseModel):
    artiste: Optional[str]
    titre: Optional[str]
    identifiants_discogs: Dict[str, Any]
    genres: List[str]
    styles: List[str]
    annee: Optional[int]
    label: Optional[List[LabelInfo]] = None
    pochette: Optional[str] = None

async def fetch_discogs_release(release_id: int) -> DiscogsMasterResponse:
    """Appelle l'API Discogs et extrait les champs utiles pour une release donnée."""
    url = f"https://api.discogs.com/releases/{release_id}"
    headers = get_discogs_headers()
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Release non trouvée sur Discogs")
        data = response.json()
        labels = extract_label_info(data.get("labels", []))
        pochette = extract_pochette(data.get("images", []))
        artist_id = None
        if data.get("artists") and len(data["artists"]) > 0:
            artist_id = data["artists"][0].get("id")
        return DiscogsMasterResponse(
            artiste=data["artists"][0]["name"] if data.get("artists") else None,
            titre=data.get("title"),
            identifiants_discogs={
                "release_id": data.get("id"),
                "artist_id": artist_id,
            },
            genres=data.get("genres", []),
            styles=data.get("styles", []),
            annee=data.get("year"),
            label=labels,
            pochette=pochette,
        )

from fastapi import Header, Depends
from dotenv import load_dotenv
load_dotenv()
import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi import Path
from user_endpoints import router as user_router

import httpx
from pydantic import BaseModel, Field

from db import SessionLocal
from models import Artist, Label, Album
from sqlalchemy import select
import asyncio
from fastapi import status
import logging

logger = logging.getLogger("disco2000")
logging.basicConfig(level=logging.INFO)

from fastapi.middleware.cors import CORSMiddleware
from db import Base, engine
from contextlib import asynccontextmanager
import os  # Import os to access environment variables

# Récupère les origines autorisées depuis la variable d'environnement ALLOW_ORIGINS
origins = os.getenv("ALLOW_ORIGINS", "*").split(",")

# Clé API à définir dans .env ou en dur pour l'exemple
API_KEY = os.getenv("API_KEY")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Clé API invalide")
    
@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Migration des tables effectuée.")
    yield

app = FastAPI(
    title="Vercel + FastAPI",
    description="Vercel + FastAPI",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Utilise les origines dynamiques
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(user_router)


# --- Endpoints albums déplacés dans album_endpoints.py ---
from album_endpoints import router as album_router
from collection_endpoints import router as collection_router
app.include_router(album_router)
app.include_router(collection_router)
    
# Endpoint pour obtenir la liste des artistes (à placer à la fin du fichier)
@app.get("/api/artists")
async def get_artists():
    async with SessionLocal() as session:
        res = await session.execute(select(Artist))
        artists = res.scalars().all()
        return [{"id": a.id, "name": a.name, "discogs_id": a.discogs_id} for a in artists]

class LabelInfo(BaseModel):
    name: str
    id: Optional[int] = None
    catno: Optional[str] = None

class DiscogsMasterResponse(BaseModel):
    artiste: Optional[str]
    titre: Optional[str]
    identifiants_discogs: Dict[str, Any]
    genres: List[str]
    styles: List[str]
    annee: Optional[int]
    label: List[LabelInfo]
    pochette: Optional[str]

def get_discogs_headers() -> Dict[str, str]:
    """Construit les headers pour l'API Discogs."""
    headers = {"User-Agent": "disco2000-api/1.0 (https://github.com/cayel/disco2000-api)"}
    token = os.getenv("DISCOGS_TOKEN")
    if token:
        headers["Authorization"] = f"Discogs token={token}"
    return headers

def extract_label_info(label_list: List[dict]) -> List[LabelInfo]:
    """Extrait les infos utiles des labels (name, id, catno), sans doublons."""
    seen = set()
    result = []
    for l in label_list:
        name = l.get("name")
        if name and name not in seen:
            seen.add(name)
            result.append(LabelInfo(name=name, id=l.get("id"), catno=l.get("catno")))
    return result

def extract_pochette(images: List[dict]) -> Optional[str]:
    """Retourne l'URL de la pochette principale ou la première image."""
    if not images:
        return None
    primary = next((img for img in images if img.get("type") == "primary" and img.get("uri")), None)
    return primary["uri"] if primary else images[0].get("uri")

async def fetch_discogs_master(master_id: int) -> DiscogsMasterResponse:
    """Appelle l'API Discogs et extrait les champs utiles pour un master donné. Complète le label via la main_release si besoin."""
    url = f"https://api.discogs.com/masters/{master_id}"
    headers = get_discogs_headers()
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Master non trouvé sur Discogs")
        data = response.json()
        labels = extract_label_info(data.get("labels", []))
        # Si pas de label sur le master, aller chercher sur la main_release
        if not labels and data.get("main_release"):
            rel_url = f"https://api.discogs.com/releases/{data['main_release']}"
            rel_resp = await client.get(rel_url, headers=headers)
            if rel_resp.status_code == 200:
                rel_data = rel_resp.json()
                labels = extract_label_info(rel_data.get("labels", []))
        pochette = extract_pochette(data.get("images", []))
        # Ajoute l'id Discogs de l'artiste si présent
        artist_id = None
        if data.get("artists") and len(data["artists"]) > 0:
            artist_id = data["artists"][0].get("id")
        return DiscogsMasterResponse(
            artiste=data["artists"][0]["name"] if data.get("artists") else None,
            titre=data.get("title"),
            identifiants_discogs={
                "master_id": data.get("id"),
                "main_release": data.get("main_release"),
                "artist_id": artist_id,
            },
            genres=data.get("genres", []),
            styles=data.get("styles", []),
            annee=data.get("year"),
            label=labels,
            pochette=pochette,
        )


# Endpoint unifié pour récupérer un master ou une release Discogs
from fastapi import Query
@app.get("/api/discogs/album/{discogs_id}", response_model=DiscogsMasterResponse)
async def get_discogs_album(discogs_id: int, type: str = Query("master", enum=["master", "release"])):
    """Endpoint public pour obtenir les infos d'un master ou d'une release Discogs par son id."""
    if type == "master":
        return await fetch_discogs_master(discogs_id)
    else:
        return await fetch_discogs_release(discogs_id)

@app.get("/api/data")
def get_sample_data():
    return {
        "data": [
            {"id": 1, "name": "Sample Item 1", "value": 100},
            {"id": 2, "name": "Sample Item 2", "value": 200},
            {"id": 3, "name": "Sample Item 3", "value": 300}
        ],
        "total": 3,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    return {
        "item": {
            "id": item_id,
            "name": "Sample Item " + str(item_id),
            "value": item_id * 100
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vercel + FastAPI</title>
        <link rel="icon" type="image/x-icon" href="/favicon.ico">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                background-color: #000000;
                color: #ffffff;
                line-height: 1.6;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }

            header {
                border-bottom: 1px solid #333333;
                padding: 0;
            }

            nav {
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                align-items: center;
                padding: 1rem 2rem;
                gap: 2rem;
            }

            .logo {
                font-size: 1.25rem;
                font-weight: 600;
                color: #ffffff;
                text-decoration: none;
            }

            .nav-links {
                display: flex;
                gap: 1.5rem;
                margin-left: auto;
            }

            .nav-links a {
                text-decoration: none;
                color: #888888;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                transition: all 0.2s ease;
                font-size: 0.875rem;
                font-weight: 500;
            }

            .nav-links a:hover {
                color: #ffffff;
                background-color: #111111;
            }

            main {
                flex: 1;
                max-width: 1200px;
                margin: 0 auto;
                padding: 4rem 2rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
            }

            .hero {
                margin-bottom: 3rem;
            }

            .hero-code {
                margin-top: 2rem;
                width: 100%;
                max-width: 900px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            }

            .hero-code pre {
                background-color: #0a0a0a;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 1.5rem;
                text-align: left;
                grid-column: 1 / -1;
            }

            h1 {
                font-size: 3rem;
                font-weight: 700;
                margin-bottom: 1rem;
                background: linear-gradient(to right, #ffffff, #888888);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }

            .subtitle {
                font-size: 1.25rem;
                color: #888888;
                margin-bottom: 2rem;
                max-width: 600px;
            }

            .cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                width: 100%;
                max-width: 900px;
            }

            .card {
                background-color: #111111;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 1.5rem;
                transition: all 0.2s ease;
                text-align: left;
            }

            .card:hover {
                border-color: #555555;
                transform: translateY(-2px);
            }

            .card h3 {
                font-size: 1.125rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #ffffff;
            }

            .card p {
                color: #888888;
                font-size: 0.875rem;
                margin-bottom: 1rem;
            }

            .card a {
                display: inline-flex;
                align-items: center;
                color: #ffffff;
                text-decoration: none;
                font-size: 0.875rem;
                font-weight: 500;
                padding: 0.5rem 1rem;
                background-color: #222222;
                border-radius: 6px;
                border: 1px solid #333333;
                transition: all 0.2s ease;
            }

            .card a:hover {
                background-color: #333333;
                border-color: #555555;
            }

            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background-color: #0070f3;
                color: #ffffff;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 500;
                margin-bottom: 2rem;
            }

            .status-dot {
                width: 6px;
                height: 6px;
                background-color: #00ff88;
                border-radius: 50%;
            }

            pre {
                background-color: #0a0a0a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 1rem;
                overflow-x: auto;
                margin: 0;
            }

            code {
                font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                font-size: 0.85rem;
                line-height: 1.5;
                color: #ffffff;
            }

            /* Syntax highlighting */
            .keyword {
                color: #ff79c6;
            }

            .string {
                color: #f1fa8c;
            }

            .function {
                color: #50fa7b;
            }

            .class {
                color: #8be9fd;
            }

            .module {
                color: #8be9fd;
            }

            .variable {
                color: #f8f8f2;
            }

            .decorator {
                color: #ffb86c;
            }

            @media (max-width: 768px) {
                nav {
                    padding: 1rem;
                    flex-direction: column;
                    gap: 1rem;
                }

                .nav-links {
                    margin-left: 0;
                }

                main {
                    padding: 2rem 1rem;
                }

                h1 {
                    font-size: 2rem;
                }

                .hero-code {
                    grid-template-columns: 1fr;
                }

                .cards {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <header>
            <nav>
                <a href="/" class="logo">Vercel + FastAPI</a>
                <div class="nav-links">
                    <a href="/docs">API Docs</a>
                    <a href="/api/data">API</a>
                </div>
            </nav>
        </header>
        <main>
            <div class="hero">
                <h1>Vercel + FastAPI</h1>
                <div class="hero-code">
                    <pre><code><span class="keyword">from</span> <span class="module">fastapi</span> <span class="keyword">import</span> <span class="class">FastAPI</span>

<span class="variable">app</span> = <span class="class">FastAPI</span>()

<span class="decorator">@app.get</span>(<span class="string">"/"</span>)
<span class="keyword">def</span> <span class="function">read_root</span>():
    <span class="keyword">return</span> {<span class="string">"Python"</span>: <span class="string">"on Vercel"</span>}</code></pre>
                </div>
            </div>

            <div class="cards">
                <div class="card">
                    <h3>Interactive API Docs</h3>
                    <p>Explore this API's endpoints with the interactive Swagger UI. Test requests and view response schemas in real-time.</p>
                    <a href="/docs">Open Swagger UI →</a>
                </div>

                <div class="card">
                    <h3>Sample Data</h3>
                    <p>Access sample JSON data through our REST API. Perfect for testing and development purposes.</p>
                    <a href="/api/data">Get Data →</a>
                </div>

            </div>
        </main>
    </body>
    </html>
    """

# Endpoint pour ajouter un album studio à partir d'un master Discogs

from auth_dependencies import get_current_user_contributeur

@app.post("/api/albums/studio", status_code=status.HTTP_201_CREATED)
async def add_studio_album(master_id: int, user=Depends(get_current_user_contributeur)):
    logger.info(f"Début ajout album studio pour master Discogs {master_id}")
    try:
        master = await fetch_discogs_master(master_id)
        logger.info(f"Infos master récupérées : titre={master.titre}, artiste={master.artiste}")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du master Discogs {master_id} : {e}")
        raise HTTPException(status_code=500, detail=str(e))
    from sqlalchemy.exc import IntegrityError
    async with SessionLocal() as session:
        # Artiste : unique par nom
        artist_obj = None
        if master.artiste:
            res = await session.execute(select(Artist).where(Artist.name == master.artiste))
            artist_obj = res.scalar_one_or_none()
            if not artist_obj:
                # Récupère le discogs_id de l'artiste si présent dans master
                discogs_artist_id = None
                if hasattr(master, 'identifiants_discogs') and master.identifiants_discogs:
                    # On tente de récupérer l'id de l'artiste dans la structure du master
                    # (souvent master.identifiants_discogs["artist_id"] ou similaire)
                    discogs_artist_id = master.identifiants_discogs.get("artist_id")
                # Si pas trouvé, tente de le récupérer dans master (si enrichi)
                if not discogs_artist_id and hasattr(master, 'artist_id'):
                    discogs_artist_id = getattr(master, 'artist_id')
                artist_obj = Artist(name=master.artiste, discogs_id=discogs_artist_id)
                session.add(artist_obj)
                await session.flush()
                logger.info(f"Nouvel artiste inséré : {artist_obj.name} (id={artist_obj.id}, discogs_id={artist_obj.discogs_id})")
            else:
                logger.info(f"Artiste déjà existant : {artist_obj.name} (id={artist_obj.id}, discogs_id={artist_obj.discogs_id})")
        # Label : unique par discogs_id
        label_obj = None
        if master.label:
            label_info = master.label[0]
            res = await session.execute(select(Label).where(Label.discogs_id == label_info.id))
            label_obj = res.scalar_one_or_none()
            if not label_obj:
                label_obj = Label(name=label_info.name, discogs_id=label_info.id)
                session.add(label_obj)
                await session.flush()
                logger.info(f"Nouveau label inséré : {label_obj.name} (id={label_obj.id})")
            else:
                logger.info(f"Label déjà existant : {label_obj.name} (id={label_obj.id})")
        # Vérifie si l'album existe déjà (par discogs_master_id)
        res_album = await session.execute(select(Album).where(Album.discogs_master_id == master.identifiants_discogs["master_id"]))
        album_exist = res_album.scalar_one_or_none()
        if album_exist:
            logger.info(f"Album déjà existant : {album_exist.title} (id={album_exist.id})")
            raise HTTPException(status_code=409, detail="L'album existe déjà dans la base de données.")
        # Album
        album = Album(
            title=master.titre,
            discogs_master_id=master.identifiants_discogs["master_id"],
            year=master.annee,
            genre=master.genres if master.genres else [],
            style=master.styles if master.styles else [],
            cover_url=master.pochette,
            catno=label_info.catno if label_obj and hasattr(label_info, 'catno') else None,
            type="Studio",
            artist_id=artist_obj.id if artist_obj else None,
            label_id=label_obj.id if label_obj else None,
        )
        session.add(album)
        try:
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Erreur d'intégrité lors de l'ajout de l'album : {e}")
            raise HTTPException(status_code=409, detail="L'album existe déjà dans la base de données.")
        logger.info(f"Album studio ajouté : {album.title} (id={album.id})")
        return {"message": "Album studio ajouté", "album_id": album.id}
