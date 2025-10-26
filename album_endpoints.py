from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy import select
from db import SessionLocal
from models import Album, Artist, Label
from auth_dependencies import get_current_user_contributeur
import logging

logger = logging.getLogger("disco2000")

router = APIRouter()

@router.delete("/api/albums/{album_id}", status_code=204)
async def delete_album(album_id: int = Path(..., description="ID de l'album à supprimer"), user=Depends(get_current_user_contributeur)):
    async with SessionLocal() as session:
        album = await session.get(Album, album_id)
        if not album:
            raise HTTPException(status_code=404, detail="Album non trouvé")
        await session.delete(album)
        await session.commit()
        return None

@router.get("/api/albums")
async def get_albums():
    async with SessionLocal() as session:
        res = await session.execute(select(Album).order_by(Album.year.desc()))
        albums = res.scalars().all()
        result = []
        for album in albums:
            artist_name = None
            if album.artist_id:
                artist = await session.get(Artist, album.artist_id)
                if artist:
                    artist_name = artist.name
            result.append({
                "id": album.id,
                "artist": artist_name,
                "title": album.title,
                "year": album.year,
                "cover_url": album.cover_url
            })
        return result

@router.post("/api/albums/studio", status_code=status.HTTP_201_CREATED)
async def add_studio_album(master_id: int, user=Depends(get_current_user_contributeur)):
    logger.info(f"Début ajout album studio pour master Discogs {master_id}")
    try:
        from main import fetch_discogs_master  # pour éviter import circulaire
        master = await fetch_discogs_master(master_id)
        logger.info(f"Infos master récupérées : titre={master.titre}, artiste={master.artiste}")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du master Discogs {master_id} : {e}")
        raise HTTPException(status_code=500, detail=str(e))
    from sqlalchemy.exc import IntegrityError
    async with SessionLocal() as session:
        artist_obj = None
        if master.artiste:
            res = await session.execute(select(Artist).where(Artist.name == master.artiste))
            artist_obj = res.scalar_one_or_none()
            if not artist_obj:
                discogs_artist_id = None
                if hasattr(master, 'identifiants_discogs') and master.identifiants_discogs:
                    discogs_artist_id = master.identifiants_discogs.get("artist_id")
                if not discogs_artist_id and hasattr(master, 'artist_id'):
                    discogs_artist_id = getattr(master, 'artist_id')
                artist_obj = Artist(name=master.artiste, discogs_id=discogs_artist_id)
                session.add(artist_obj)
                await session.flush()
                logger.info(f"Nouvel artiste inséré : {artist_obj.name} (id={artist_obj.id}, discogs_id={artist_obj.discogs_id})")
            else:
                logger.info(f"Artiste déjà existant : {artist_obj.name} (id={artist_obj.id}, discogs_id={artist_obj.discogs_id})")
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
        res_album = await session.execute(select(Album).where(Album.discogs_master_id == master.identifiants_discogs["master_id"]))
        album_exist = res_album.scalar_one_or_none()
        if album_exist:
            logger.info(f"Album déjà existant : {album_exist.title} (id={album_exist.id})")
            raise HTTPException(status_code=409, detail="L'album existe déjà dans la base de données.")
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


# --- Endpoint détaillé après la définition de router ---

@router.get("/api/albums/{album_id}")
async def get_album_details(album_id: int):
    async with SessionLocal() as session:
        album = await session.get(Album, album_id)
        if not album:
            raise HTTPException(status_code=404, detail="Album non trouvé")
        artist = None
        label = None
        if album.artist_id:
            artist = await session.get(Artist, album.artist_id)
        if album.label_id:
            label = await session.get(Label, album.label_id)
        return {
            "id": album.id,
            "title": album.title,
            "year": album.year,
            "genre": album.genre,
            "style": album.style,
            "cover_url": album.cover_url,
            "catno": album.catno,
            "type": album.type,
            "discogs_master_id": album.discogs_master_id,
            "artist": {
                "id": artist.id,
                "name": artist.name,
                "discogs_id": artist.discogs_id
            } if artist else None,
            "label": {
                "id": label.id,
                "name": label.name,
                "discogs_id": label.discogs_id
            } if label else None
        }