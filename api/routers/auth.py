"""Google OAuth2 + JWT auth routes."""
from __future__ import annotations

import json
import time

import jwt
import requests
from fastapi import APIRouter, Cookie, HTTPException, Response
from fastapi.responses import RedirectResponse

from api.config import (
    ADMINS,
    ALLOWED_USERS,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    LOCAL_DEV,
    OAUTH_REDIRECT_URI,
    TOKEN_KEY,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

_GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v2/userinfo"

_COOKIE = "bond_jwt"
_EXP    = 60 * 60 * 24 * 7  # 7 days


def _make_jwt(email: str) -> str:
    payload = {
        "email": email,
        "is_admin": email in ADMINS,
        "iat": int(time.time()),
        "exp": int(time.time()) + _EXP,
    }
    return jwt.encode(payload, TOKEN_KEY, algorithm="HS256")


def _decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, TOKEN_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/login")
def login() -> RedirectResponse:
    if LOCAL_DEV:
        resp = RedirectResponse(url="/")
        resp.set_cookie(_COOKIE, _make_jwt("local@dev"), httponly=True, max_age=_EXP)
        return resp
    params = (
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={OAUTH_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&access_type=offline"
    )
    return RedirectResponse(url=f"{_GOOGLE_AUTH_URL}?{params}")


@router.get("/callback")
def callback(code: str, response: Response) -> RedirectResponse:
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    r = requests.post(_GOOGLE_TOKEN_URL, data=token_data, timeout=15)
    if not r.ok:
        raise HTTPException(status_code=400, detail="OAuth token exchange failed")

    id_token = r.json().get("id_token", "")
    # Decode without verification just to extract email (Google already verified)
    payload = jwt.decode(id_token, options={"verify_signature": False})
    email   = payload.get("email", "")

    if ALLOWED_USERS and email not in ALLOWED_USERS:
        raise HTTPException(status_code=403, detail="User not authorised")

    resp = RedirectResponse(url="/")
    resp.set_cookie(_COOKIE, _make_jwt(email), httponly=True, max_age=_EXP)
    return resp


@router.get("/me")
def me(bond_jwt: str | None = Cookie(default=None)) -> dict:
    if LOCAL_DEV:
        return {"email": "local@dev", "is_admin": True}
    if not bond_jwt:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = _decode_jwt(bond_jwt)
    return {"email": payload["email"], "is_admin": payload.get("is_admin", False)}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(_COOKIE)
    return {"ok": True}
