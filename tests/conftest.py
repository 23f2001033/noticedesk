import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class _FakeDoc:
    def __init__(self, exists: bool, data: dict | None = None):
        self.exists = exists
        self._data = data

    def to_dict(self) -> dict | None:
        return self._data


class _FakeFirestoreClient:
    """Stands in for google.cloud.firestore.Client in dependency tests.

    Phase 0 has no real Firestore project to test against, so `collection()`
    and `document()` both return self and `get()` returns the pre-seeded doc --
    just enough chain to exercise app.deps.get_current_firm.
    """

    def __init__(self, doc: _FakeDoc):
        self._doc = doc

    def collection(self, name: str) -> "_FakeFirestoreClient":
        return self

    def document(self, doc_id: str) -> "_FakeFirestoreClient":
        return self

    def get(self) -> _FakeDoc:
        return self._doc


@pytest.fixture
def fake_firestore_with_user():
    def _make(data: dict) -> _FakeFirestoreClient:
        return _FakeFirestoreClient(_FakeDoc(exists=True, data=data))

    return _make


@pytest.fixture
def fake_firestore_no_user() -> _FakeFirestoreClient:
    return _FakeFirestoreClient(_FakeDoc(exists=False))


class _FakeWriteFirestoreClient:
    """Stands in for google.cloud.firestore.Client in write-path tests
    (e.g. app.services.logging_runs.log_agent_run) -- records every
    collection(...).document().set(data) call instead of hitting Firestore.
    """

    def __init__(self) -> None:
        self.writes: list[tuple[str, dict]] = []
        self._pending_collection: str | None = None

    def collection(self, name: str) -> "_FakeWriteFirestoreClient":
        self._pending_collection = name
        return self

    def document(self, doc_id: str | None = None) -> "_FakeWriteFirestoreClient":
        return self

    def set(self, data: dict) -> None:
        assert self._pending_collection is not None
        self.writes.append((self._pending_collection, data))


@pytest.fixture
def fake_firestore_recorder() -> _FakeWriteFirestoreClient:
    return _FakeWriteFirestoreClient()
