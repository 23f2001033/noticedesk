from functools import lru_cache

from google.cloud import firestore

from app.config import get_settings


@lru_cache
def get_firestore_client() -> firestore.Client:
    """Lazily construct the Firestore client.

    Not called at import time or in Phase 0 tests -- real reads/writes arrive
    with the Phase 1 data model (see docs/SPEC.md #3).
    """
    settings = get_settings()
    return firestore.Client(project=settings.gcp_project_id)
