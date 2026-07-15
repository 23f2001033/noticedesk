import firebase_admin
from firebase_admin import auth as firebase_auth

_app: firebase_admin.App | None = None


def _get_firebase_app() -> firebase_admin.App:
    global _app
    if _app is None:
        _app = firebase_admin.initialize_app()
    return _app


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return its decoded claims.

    Raises a firebase_admin.auth exception (e.g. InvalidIdTokenError,
    ExpiredIdTokenError) on failure -- callers translate that into a 401.
    """
    _get_firebase_app()
    return firebase_auth.verify_id_token(id_token)
