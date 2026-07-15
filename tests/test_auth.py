from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_firm, get_current_user

# app.main only exposes /healthz in Phase 0 -- these throwaway routes exercise
# the auth dependencies directly without adding unused endpoints to the real app.
_auth_test_app = FastAPI()


@_auth_test_app.get("/whoami")
def whoami(user: dict = Depends(get_current_user)) -> dict:
    return user


@_auth_test_app.get("/firm")
def firm(firm: dict = Depends(get_current_firm)) -> dict:
    return firm


auth_client = TestClient(_auth_test_app)


def test_missing_token_returns_401() -> None:
    response = auth_client.get("/whoami")

    assert response.status_code == 401


def test_invalid_token_returns_401(monkeypatch) -> None:
    def _raise(token: str) -> dict:
        raise ValueError("bad token")

    monkeypatch.setattr("app.deps.verify_firebase_token", _raise)

    response = auth_client.get("/whoami", headers={"Authorization": "Bearer bad-token"})

    assert response.status_code == 401


def test_valid_token_returns_claims(monkeypatch) -> None:
    monkeypatch.setattr("app.deps.verify_firebase_token", lambda token: {"uid": "test-uid"})

    response = auth_client.get("/whoami", headers={"Authorization": "Bearer good-token"})

    assert response.status_code == 200
    assert response.json()["uid"] == "test-uid"


def test_firm_lookup_403_without_user_record(monkeypatch, fake_firestore_no_user) -> None:
    monkeypatch.setattr("app.deps.verify_firebase_token", lambda token: {"uid": "test-uid"})
    monkeypatch.setattr("app.deps.get_firestore_client", lambda: fake_firestore_no_user)

    response = auth_client.get("/firm", headers={"Authorization": "Bearer good-token"})

    assert response.status_code == 403


def test_firm_lookup_200_with_user_record(monkeypatch, fake_firestore_with_user) -> None:
    monkeypatch.setattr("app.deps.verify_firebase_token", lambda token: {"uid": "test-uid"})
    monkeypatch.setattr(
        "app.deps.get_firestore_client",
        lambda: fake_firestore_with_user({"firm_id": "firm-1", "role": "partner"}),
    )

    response = auth_client.get("/firm", headers={"Authorization": "Bearer good-token"})

    assert response.status_code == 200
    assert response.json()["firm_id"] == "firm-1"
