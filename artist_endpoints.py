from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from db import SessionLocal
from models import Artist
from auth_dependencies import get_current_user_contributeur
from country_utils import (
    is_valid_country_code,
    normalize_country_code,
    get_country_name,
    get_all_countries
)
import logging

logger = logging.getLogger("disco2000")

router = APIRouter()


class ArtistUpdateRequest(BaseModel):
    country: str | None = None
    
    @field_validator('country')
    @classmethod
    def validate_country(cls, v: str | None) -> str | None:
        """Valide et normalise le code pays."""
        if v is None:
            return None
        
        # Normalise le code (majuscules, supprime espaces)
        normalized = normalize_country_code(v)
        
        # Vérifie la validité
        if not is_valid_country_code(normalized):
            raise ValueError(f"Code pays invalide : '{v}'. Doit être un code ISO 3166-1 alpha-2 (ex: FR, US, GB)")
        
        return normalized


@router.get("/api/countries")
async def get_countries():
    """Récupère la liste complète des pays disponibles (codes ISO 3166-1 alpha-2)."""
    return get_all_countries()


@router.get("/api/artists")
async def get_artists():
    """Récupère la liste de tous les artistes avec leurs pays."""
    async with SessionLocal() as session:
        res = await session.execute(select(Artist))
        artists = res.scalars().all()
        return [{
            "id": a.id,
            "name": a.name,
            "discogs_id": a.discogs_id,
            "country": a.country,
            "country_name": get_country_name(a.country) if a.country else None
        } for a in artists]


@router.patch("/api/artists/{artist_id}")
async def update_artist(
    artist_id: int = Path(..., description="ID de l'artiste à mettre à jour"),
    update_data: ArtistUpdateRequest = ...,
    user=Depends(get_current_user_contributeur)
):
    """Met à jour les informations d'un artiste (nécessite le rôle contributeur)."""
    async with SessionLocal() as session:
        artist = await session.get(Artist, artist_id)
        if not artist:
            raise HTTPException(status_code=404, detail="Artiste non trouvé")
        
        # Met à jour le pays si fourni (déjà validé et normalisé par Pydantic)
        if update_data.country is not None:
            artist.country = update_data.country
            country_name = get_country_name(update_data.country) if update_data.country else "aucun"
            logger.info(f"Mise à jour du pays de l'artiste {artist.name} (id={artist.id}) : {update_data.country} ({country_name})")
        
        await session.commit()
        
        return {
            "id": artist.id,
            "name": artist.name,
            "discogs_id": artist.discogs_id,
            "country": artist.country,
            "country_name": get_country_name(artist.country) if artist.country else None
        }


@router.get("/api/artists/{artist_id}")
async def get_artist(artist_id: int = Path(..., description="ID de l'artiste")):
    """Récupère les informations détaillées d'un artiste."""
    async with SessionLocal() as session:
        artist = await session.get(Artist, artist_id)
        if not artist:
            raise HTTPException(status_code=404, detail="Artiste non trouvé")
        
        return {
            "id": artist.id,
            "name": artist.name,
            "discogs_id": artist.discogs_id,
            "country": artist.country
        }
