from fastapi import Depends, HTTPException, Request, status

from app.services.auth import verify_firebase_token
from app.services.firestore import get_firestore_client


def get_current_user(request: Request) -> dict:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_firebase_token(token)
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc


def get_current_firm(user: dict = Depends(get_current_user)) -> dict:
    db = get_firestore_client()
    doc = db.collection("users").document(user["uid"]).get()
    if not doc.exists:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No firm associated with this account")
    return doc.to_dict()
