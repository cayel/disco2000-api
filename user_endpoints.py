import firebase_admin
from firebase_admin import auth as firebase_auth, credentials as firebase_credentials
import json
import os

from fastapi import APIRouter, HTTPException, Security, Query
from sqlalchemy import select
from db import SessionLocal
from models import User
from pydantic import BaseModel, EmailStr
from typing import List
from jwt_utils import create_access_token
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

router = APIRouter()

# Initialisation Firebase Admin depuis une variable d'environnement
firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
if not firebase_admin._apps:
    cred = firebase_credentials.Certificate(json.loads(firebase_json))
    firebase_admin.initialize_app(cred)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    identifier: str
    roles: List[str]

class UserExistsResponse(BaseModel):
    exists: bool

class UserInfoResponse(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    identifier: str
    roles: List[str]

class UserTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Endpoint pour obtenir un JWT applicatif à partir d'un id_token Google
class GoogleTokenRequest(BaseModel):
    id_token: str

class UserTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/api/users/token", response_model=UserTokenResponse)
async def get_user_token_google(body: GoogleTokenRequest):
    try:
        decoded_token = firebase_auth.verify_id_token(body.id_token)
        email = decoded_token["email"]
        first_name = decoded_token.get("given_name", "")
        last_name = decoded_token.get("family_name", "")
    except Exception as e:
        print(f"Erreur Google token: {e}")
        raise HTTPException(status_code=401, detail="Token Google invalide")
    # Recherche ou création de l'utilisateur en base
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            # Crée un nouvel utilisateur minimal si besoin
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                identifier=email.split("@")[0],
                roles=["utilisateur"]
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        token_data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "identifier": user.identifier,
            "roles": user.roles
        }
        access_token = create_access_token(token_data)
        return {"access_token": access_token, "token_type": "bearer"}

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