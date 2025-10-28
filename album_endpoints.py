from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy import select
from db import SessionLocal
from models import Album, Artist, Label, UserAlbumCollection
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

from fastapi import Request

@router.get("/api/albums")
async def get_albums(request: Request):
    user = None
    roles = []
    # Tente de décoder le token pour savoir si l'utilisateur est authentifié
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        from jwt_utils import decode_access_token
        token = auth_header.split(" ", 1)[1]
        payload = decode_access_token(token)
        if payload:
            user = payload
            roles = payload.get("roles", [])
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
            album_dict = {
                "id": album.id,
                "artist": artist_name,
                "title": album.title,
                "year": album.year,
                "cover_url": album.cover_url
            }
            # Ajoute les infos de collection si utilisateur authentifié et rôle utilisateur
            if user and "utilisateur" in roles:
                res_coll = await session.execute(
                    select(UserAlbumCollection).where(
                        UserAlbumCollection.user_id == user["id"],
                        UserAlbumCollection.album_id == album.id
                    )
                )
                coll = res_coll.scalar_one_or_none()
                if coll:
                    album_dict["collection"] = {"cd": coll.cd, "vinyl": coll.vinyl}
                else:
                    album_dict["collection"] = None
            result.append(album_dict)
        return result


from fastapi import Query
@router.post("/api/albums/studio", status_code=status.HTTP_201_CREATED)
async def add_album_studio(
    discogs_id: int = Query(..., description="ID Discogs master ou release"),
    discogs_type: str = Query("master", enum=["master", "release"], description="Type Discogs : master ou release"),
    user=Depends(get_current_user_contributeur)
):
    logger.info(f"Début ajout album studio pour Discogs {discogs_type} {discogs_id}")
    try:
        if discogs_type == "master":
            from main import fetch_discogs_master
            discogs_data = await fetch_discogs_master(discogs_id)
        else:
            from main import fetch_discogs_release
            discogs_data = await fetch_discogs_release(discogs_id)
        logger.info(f"Infos récupérées : titre={discogs_data.titre}, artiste={discogs_data.artiste}")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération Discogs {discogs_type} {discogs_id} : {e}")
        raise HTTPException(status_code=500, detail=str(e))
    from sqlalchemy.exc import IntegrityError
    async with SessionLocal() as session:
        artist_obj = None
        if discogs_data.artiste:
            res = await session.execute(select(Artist).where(Artist.name == discogs_data.artiste))
            artist_obj = res.scalar_one_or_none()
            if not artist_obj:
                discogs_artist_id = None
                if hasattr(discogs_data, 'identifiants_discogs') and discogs_data.identifiants_discogs:
                    discogs_artist_id = discogs_data.identifiants_discogs.get("artist_id")
                if not discogs_artist_id and hasattr(discogs_data, 'artist_id'):
                    discogs_artist_id = getattr(discogs_data, 'artist_id')
                artist_obj = Artist(name=discogs_data.artiste, discogs_id=discogs_artist_id)
                session.add(artist_obj)
                await session.flush()
                logger.info(f"Nouvel artiste inséré : {artist_obj.name} (id={artist_obj.id}, discogs_id={artist_obj.discogs_id})")
            else:
                logger.info(f"Artiste déjà existant : {artist_obj.name} (id={artist_obj.id}, discogs_id={artist_obj.discogs_id})")
        label_obj = None
        label_info = None
        if discogs_data.label:
            label_info = discogs_data.label[0]
            res = await session.execute(select(Label).where(Label.discogs_id == label_info.id))
            label_obj = res.scalar_one_or_none()
            if not label_obj:
                label_obj = Label(name=label_info.name, discogs_id=label_info.id)
                session.add(label_obj)
                await session.flush()
                logger.info(f"Nouveau label inséré : {label_obj.name} (id={label_obj.id})")
            else:
                logger.info(f"Label déjà existant : {label_obj.name} (id={label_obj.id})")
        # Vérifications croisées master/release
        if discogs_type == "master":
            # Unicité stricte sur discogs_master_id
            res_album = await session.execute(select(Album).where(Album.discogs_master_id == discogs_data.identifiants_discogs["master_id"]))
            album_exist = res_album.scalar_one_or_none()
            if album_exist:
                logger.info(f"Album déjà existant : {album_exist.title} (id={album_exist.id})")
                raise HTTPException(status_code=409, detail="L'album existe déjà dans la base de données.")
            # Vérifie qu'aucune release n'existe déjà pour même titre, artiste, année
            res_release = await session.execute(
                select(Album).where(
                    Album.title == discogs_data.titre,
                    Album.year == discogs_data.annee,
                    Album.artist_id == (artist_obj.id if artist_obj else None),
                    Album.discogs_link_type == "release"
                )
            )
            release_exist = res_release.scalar_one_or_none()
            if release_exist:
                logger.info(f"Release déjà existante pour ce titre/artiste/année : {release_exist.title} (id={release_exist.id})")
                raise HTTPException(status_code=409, detail="Une release existe déjà pour ce titre, artiste et année. Impossible d'ajouter le master.")
            discogs_link_type = "master"
            discogs_master_id = discogs_data.identifiants_discogs["master_id"]
        else:
            # Refuse si un master existe déjà pour même titre, artiste, année
            res_master = await session.execute(
                select(Album).where(
                    Album.title == discogs_data.titre,
                    Album.year == discogs_data.annee,
                    Album.artist_id == (artist_obj.id if artist_obj else None),
                    Album.discogs_link_type == "master"
                )
            )
            master_exist = res_master.scalar_one_or_none()
            if master_exist:
                logger.info(f"Master déjà existant pour ce titre/artiste/année : {master_exist.title} (id={master_exist.id})")
                raise HTTPException(status_code=409, detail="Un master existe déjà pour ce titre, artiste et année. Impossible d'ajouter la release.")
            discogs_link_type = "release"
            discogs_master_id = None
        album = Album(
            title=discogs_data.titre,
            discogs_master_id=discogs_master_id,
            year=discogs_data.annee,
            genre=discogs_data.genres if discogs_data.genres else [],
            style=discogs_data.styles if discogs_data.styles else [],
            cover_url=discogs_data.pochette,
            catno=label_info.catno if label_obj and label_info and hasattr(label_info, 'catno') else None,
            type="Studio",
            artist_id=artist_obj.id if artist_obj else None,
            label_id=label_obj.id if label_obj else None,
            discogs_link_type=discogs_link_type
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

from fastapi import Request

@router.get("/api/albums/{album_id}")
async def get_album_details(album_id: int, request: Request):
    user = None
    roles = []
    # Tente de décoder le token pour savoir si l'utilisateur est authentifié
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        from jwt_utils import decode_access_token
        token = auth_header.split(" ", 1)[1]
        payload = decode_access_token(token)
        if payload:
            user = payload
            roles = payload.get("roles", [])
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
        album_dict = {
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
        # Ajoute les infos de collection si utilisateur authentifié et rôle utilisateur
        if user and "utilisateur" in roles:
            from models import UserAlbumCollection
            res_coll = await session.execute(
                select(UserAlbumCollection).where(
                    UserAlbumCollection.user_id == user["id"],
                    UserAlbumCollection.album_id == album.id
                )
            )
            coll = res_coll.scalar_one_or_none()
            if coll:
                album_dict["collection"] = {"cd": coll.cd, "vinyl": coll.vinyl}
            else:
                album_dict["collection"] = None
        return album_dict
    
