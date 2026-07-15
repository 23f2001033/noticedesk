from datetime import UTC, datetime, timedelta

from app.agents.classifier import ClassifierResult
from app.models.case import CaseSource, CaseStatus, NoticeType
from app.models.extraction import Extraction
from app.services import case_pipeline
from app.services.ocr import OcrResult


class _FakeDocRef:
    def __init__(self, doc_id: str, writes: list[tuple[str, dict]], path: str) -> None:
        self.id = doc_id
        self._writes = writes
        self._path = path

    def set(self, data: dict) -> None:
        self._writes.append((self._path, data))

    def collection(self, name: str) -> "_FakeCollection":
        return _FakeCollection(name, self._writes, self._path)


class _FakeCollection:
    def __init__(self, name: str, writes: list[tuple[str, dict]], parent_path: str = "") -> None:
        self._name = name
        self._writes = writes
        self._parent_path = parent_path
        self._auto_counter = 0

    def document(self, doc_id: str | None = None) -> _FakeDocRef:
        if doc_id is None:
            self._auto_counter += 1
            doc_id = f"auto-{self._auto_counter}"
        prefix = f"{self._parent_path}/" if self._parent_path else ""
        return _FakeDocRef(doc_id, self._writes, f"{prefix}{self._name}/{doc_id}")


class _FakeFirestoreDB:
    def __init__(self) -> None:
        self.writes: list[tuple[str, dict]] = []

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(name, self.writes)


def _patch_common(monkeypatch, fake_db, *, ocr_used: bool = False, pages: int = 1):
    monkeypatch.setattr("app.services.case_pipeline.get_firestore_client", lambda: fake_db)
    monkeypatch.setattr(
        "app.services.case_pipeline.upload_document", lambda **kwargs: "gs://bucket/path"
    )
    monkeypatch.setattr(
        "app.services.case_pipeline.route_ocr",
        lambda **kwargs: OcrResult(text="notice text", ocr_used=ocr_used, pages=pages),
    )


def test_ingest_notice_uses_extracted_due_date(monkeypatch) -> None:
    fake_db = _FakeFirestoreDB()
    _patch_common(monkeypatch, fake_db)
    monkeypatch.setattr(
        "app.services.case_pipeline.classify_notice",
        lambda **kwargs: ClassifierResult(notice_type=NoticeType.ASMT_10, confidence=0.9),
    )
    explicit_due = datetime(2026, 8, 1, tzinfo=UTC)
    monkeypatch.setattr(
        "app.services.case_pipeline.extract_notice",
        lambda **kwargs: Extraction(
            notice_date=datetime(2026, 7, 1, tzinfo=UTC), due_date=explicit_due
        ),
    )

    case = case_pipeline.ingest_notice(
        firm_id="firm-1",
        client_id="client-1",
        uploaded_by="uid-1",
        file_bytes=b"pdf-bytes",
        filename="notice.pdf",
        content_type="application/pdf",
    )

    assert case.due_date == explicit_due
    assert case.due_date_source == "extracted"
    assert case.due_date_confirmed is False
    assert case.notice_type == NoticeType.ASMT_10
    assert case.status == CaseStatus.NEW
    assert case.source == CaseSource.WEB
    assert len(fake_db.writes) == 3  # case doc, documents doc, extraction doc


def test_ingest_notice_computes_statutory_default_due_date(monkeypatch) -> None:
    fake_db = _FakeFirestoreDB()
    _patch_common(monkeypatch, fake_db, ocr_used=True, pages=2)
    monkeypatch.setattr(
        "app.services.case_pipeline.classify_notice",
        lambda **kwargs: ClassifierResult(notice_type=NoticeType.ASMT_10, confidence=0.9),
    )
    notice_date = datetime(2026, 7, 1, tzinfo=UTC)
    monkeypatch.setattr(
        "app.services.case_pipeline.extract_notice",
        lambda **kwargs: Extraction(notice_date=notice_date, due_date=None),
    )

    case = case_pipeline.ingest_notice(
        firm_id="firm-1",
        client_id="client-1",
        uploaded_by="uid-1",
        file_bytes=b"pdf-bytes",
        filename="notice.pdf",
        content_type="application/pdf",
    )

    assert case.due_date == notice_date + timedelta(days=30)
    assert case.due_date_source == "statutory_default"
    assert case.due_date_confirmed is False


def test_ingest_notice_leaves_due_date_none_when_notice_date_missing(monkeypatch) -> None:
    fake_db = _FakeFirestoreDB()
    _patch_common(monkeypatch, fake_db, ocr_used=True, pages=1)
    monkeypatch.setattr(
        "app.services.case_pipeline.classify_notice",
        lambda **kwargs: ClassifierResult(notice_type=NoticeType.OTHER, confidence=0.2),
    )
    monkeypatch.setattr("app.services.case_pipeline.extract_notice", lambda **kwargs: Extraction())

    case = case_pipeline.ingest_notice(
        firm_id="firm-1",
        client_id="client-1",
        uploaded_by="uid-1",
        file_bytes=b"pdf-bytes",
        filename="notice.pdf",
        content_type="application/pdf",
    )

    assert case.due_date is None
    assert case.due_date_source is None
    assert case.due_date_confirmed is False
