from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from db import SessionLocal
from models import UserAlbumCollection, Album, Artist
from auth_dependencies import get_current_user_utilisateur

router = APIRouter()

@router.get("/api/collection/stats")
async def get_collection_stats(user=Depends(get_current_user_utilisateur)):
    async with SessionLocal() as session:
        # Récupère tous les albums de la collection de l'utilisateur
        res = await session.execute(
            select(UserAlbumCollection, Album, Artist)
            .join(Album, UserAlbumCollection.album_id == Album.id)
            .join(Artist, Album.artist_id == Artist.id)
            .where(UserAlbumCollection.user_id == user["id"])
        )
        rows = res.all()
        total_discs = len(rows)
        total_cd = sum(1 for row in rows if row[0].cd)
        total_vinyl = sum(1 for row in rows if row[0].vinyl)
        # Stat artiste le plus représenté
        artist_count = {}
        for row in rows:
            artist_name = row[2].name if row[2] else None
            if artist_name:
                artist_count[artist_name] = artist_count.get(artist_name, 0) + 1
        top_artist = max(artist_count.items(), key=lambda x: x[1]) if artist_count else (None, 0)
        # Stat année la plus représentée
        year_count = {}
        for row in rows:
            year = row[1].year if row[1] else None
            if year:
                year_count[year] = year_count.get(year, 0) + 1
        top_year = max(year_count.items(), key=lambda x: x[1]) if year_count else (None, 0)
        return {
            "total_discs": total_discs,
            "total_cd": total_cd,
            "total_vinyl": total_vinyl,
            "top_artist": top_artist[0],
            "top_artist_count": top_artist[1],
            "top_year": top_year[0],
            "top_year_count": top_year[1]
        }
