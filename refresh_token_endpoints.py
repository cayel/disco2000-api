from fastapi import APIRouter, HTTPException, Request
from jwt_utils import decode_refresh_token, create_access_token, create_refresh_token

router = APIRouter()

@router.post("/api/users/refresh")
async def refresh_token(request: Request):
    data = await request.json()
    refresh_token = data.get("refresh_token")
    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expiré")
    # On retire les champs spécifiques du refresh token
    token_data = {k: v for k, v in payload.items() if k not in ("exp", "type", "iat")}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
