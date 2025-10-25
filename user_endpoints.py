from fastapi import Query

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from db import SessionLocal
from models import User
from pydantic import BaseModel, EmailStr
from typing import List

router = APIRouter()

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    identifier: str
    roles: List[str]

class UserExistsResponse(BaseModel):
    exists: bool
    
# Endpoint pour tester si un utilisateur existe à partir de son email
@router.get("/api/users/exists", response_model=UserExistsResponse)
async def user_exists(email: EmailStr = Query(...)):
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        return {"exists": user is not None}
    
@router.post("/api/users", status_code=201)
async def create_user(user: UserCreate):
    async with SessionLocal() as session:
        existing = await session.execute(
            select(User).where((User.email == user.email) | (User.identifier == user.identifier))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email ou identifiant déjà utilisé")
        db_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            identifier=user.identifier,
            roles=user.roles
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return {
            "id": db_user.id,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "email": db_user.email,
            "identifier": db_user.identifier,
            "roles": db_user.roles
        }

@router.get("/api/users")
async def list_users():
    async with SessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return [
            {
                "id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "identifier": u.identifier,
                "roles": u.roles
            }
            for u in users
        ]