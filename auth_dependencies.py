from fastapi import Header, HTTPException, Depends, Request
from jwt_utils import decode_access_token

def get_current_user_contributeur(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token d'authentification manquant ou invalide")
    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token d'authentification invalide")
    roles = payload.get("roles", [])
    if "contributeur" not in roles:
        raise HTTPException(status_code=403, detail="Droits insuffisants : rôle 'contributeur' requis")
    return payload
