
import logging
from fastapi import APIRouter
from sqlalchemy import select, func
from db import SessionLocal
from models import Album, Artist
from pydantic import BaseModel
from typing import List, Optional


logger = logging.getLogger("disco2000.public_stats")
router = APIRouter()

class AlbumsPerYear(BaseModel):
    year: Optional[int]
    count: int

class PublicCollectionStatsResponse(BaseModel):
    total_albums: int
    total_artists: int
    top_artist: Optional[str]
    top_artist_count: int
    top_year: Optional[int]
    top_year_count: int
    albums_per_year: List[AlbumsPerYear]

@router.get("/api/albums/stats", response_model=PublicCollectionStatsResponse)
async def get_public_collection_stats():
    async with SessionLocal() as session:
        # Nombre total d'albums
        res_albums = await session.execute(select(func.count(Album.id)))
        total_albums = res_albums.scalar() or 0
        # Nombre total d'artistes
        res_artists = await session.execute(select(func.count(Artist.id)))
        total_artists = res_artists.scalar() or 0
        # Artiste le plus représenté
        res_top_artist = await session.execute(
            select(Artist.name, func.count(Album.id).label("nb"))
            .join(Album, Album.artist_id == Artist.id)
            .group_by(Artist.name)
            .order_by(func.count(Album.id).desc())
            .limit(1)
        )
        top_artist_row = res_top_artist.first()
        top_artist = top_artist_row[0] if top_artist_row else None
        top_artist_count = top_artist_row[1] if top_artist_row else 0
        # Année la plus représentée
        res_top_year = await session.execute(
            select(Album.year, func.count(Album.id).label("nb"))
            .group_by(Album.year)
            .order_by(func.count(Album.id).desc())
            .limit(1)
        )
        top_year_row = res_top_year.first()
        top_year = top_year_row[0] if top_year_row else None
        top_year_count = top_year_row[1] if top_year_row else 0
        # Nombre d'albums par année
        res_years = await session.execute(
            select(Album.year, func.count(Album.id))
            .group_by(Album.year)
            .order_by(Album.year)
        )
        albums_per_year = [
            AlbumsPerYear(year=row[0], count=row[1]) for row in res_years.fetchall() if row[0] is not None
        ]
        # Debug : afficher la réponse brute
        debug_response = {
            "total_albums": total_albums or 0,
            "total_artists": total_artists or 0,
            "top_artist": top_artist or None,
            "top_artist_count": top_artist_count or 0,
            "top_year": top_year or None,
            "top_year_count": top_year_count or 0,
            "albums_per_year": [AlbumsPerYear(year=ap.year, count=ap.count) for ap in albums_per_year] if albums_per_year else []
        }
        logger.warning("[DEBUG /api/albums/stats] %s", debug_response)
        return PublicCollectionStatsResponse(**debug_response)
