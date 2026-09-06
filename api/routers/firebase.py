"""Firebase Firestore routes for saved formulas."""
from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException
from pydantic import BaseModel

from api.config import LOCAL_DEV, TOKEN_KEY
import jwt

router = APIRouter(prefix="/api", tags=["firebase"])


def _get_email(bond_jwt: str | None = Cookie(default=None)) -> str:
    if LOCAL_DEV:
        return "local@dev"
    if not bond_jwt:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(bond_jwt, TOKEN_KEY, algorithms=["HS256"])
        return payload["email"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


try:
    from firebase_utils import get_formula_list, add_formula, delete_formula  # type: ignore
    _FIREBASE_OK = True
except Exception:
    _FIREBASE_OK = False


class FormulaBody(BaseModel):
    formula: str


@router.get("/formulas")
def list_formulas(email: str = Depends(_get_email)) -> list[str]:
    if not _FIREBASE_OK:
        return []
    return get_formula_list(email)


@router.post("/formulas")
def create_formula(body: FormulaBody, email: str = Depends(_get_email)) -> dict:
    if not _FIREBASE_OK:
        raise HTTPException(status_code=503, detail="Firebase not configured")
    add_formula(email, body.formula)
    return {"ok": True}


@router.delete("/formulas/{formula_id}")
def remove_formula(formula_id: str, email: str = Depends(_get_email)) -> dict:
    if not _FIREBASE_OK:
        raise HTTPException(status_code=503, detail="Firebase not configured")
    delete_formula(email, formula_id)
    return {"ok": True}
