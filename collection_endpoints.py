from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from db import SessionLocal
from models import UserAlbumCollection, Album
from auth_dependencies import get_current_user_utilisateur
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CollectionUpdateRequest(BaseModel):
    album_id: int
    cd: Optional[bool] = False
    vinyl: Optional[bool] = False

@router.post("/api/collection", status_code=status.HTTP_200_OK)
async def add_or_update_collection(
    req: CollectionUpdateRequest,
    user=Depends(get_current_user_utilisateur)
):
    async with SessionLocal() as session:
        # Vérifie que l'album existe
        album = await session.get(Album, req.album_id)
        if not album:
            raise HTTPException(status_code=404, detail="Album non trouvé")
        # Cherche une entrée existante
        res = await session.execute(
            select(UserAlbumCollection).where(
                UserAlbumCollection.user_id == user["id"],
                UserAlbumCollection.album_id == req.album_id
            )
        )
        entry = res.scalar_one_or_none()
        if entry:
            entry.cd = req.cd
            entry.vinyl = req.vinyl
        else:
            entry = UserAlbumCollection(user_id=user["id"], album_id=req.album_id, cd=req.cd, vinyl=req.vinyl)
            session.add(entry)
        await session.commit()
        return {"message": "Collection mise à jour", "album_id": req.album_id, "cd": entry.cd, "vinyl": entry.vinyl}

@router.get("/api/collection", status_code=status.HTTP_200_OK)
async def get_user_collection(user=Depends(get_current_user_utilisateur)):
    async with SessionLocal() as session:
        res = await session.execute(
            select(UserAlbumCollection).where(UserAlbumCollection.user_id == user["id"])
        )
        collection = res.scalars().all()
        return [
            {"album_id": c.album_id, "cd": c.cd, "vinyl": c.vinyl}
            for c in collection
        ]
