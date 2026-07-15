from types import SimpleNamespace

import pytest

from app.services.storage import upload_document


class _FakeBlob:
    def __init__(self) -> None:
        self.uploaded: tuple[bytes, str] | None = None

    def upload_from_string(self, data: bytes, content_type: str | None = None) -> None:
        self.uploaded = (data, content_type)


class _FakeBucket:
    def __init__(self) -> None:
        self.blobs: dict[str, _FakeBlob] = {}

    def blob(self, path: str) -> _FakeBlob:
        blob = _FakeBlob()
        self.blobs[path] = blob
        return blob


class _FakeStorageClient:
    def __init__(self) -> None:
        self.bucket_obj = _FakeBucket()

    def bucket(self, name: str) -> _FakeBucket:
        return self.bucket_obj


def test_upload_document_returns_gs_uri(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.storage.get_settings",
        lambda: SimpleNamespace(cloud_storage_bucket="test-bucket"),
    )
    fake_client = _FakeStorageClient()
    monkeypatch.setattr("app.services.storage.get_storage_client", lambda: fake_client)

    ref = upload_document(
        file_bytes=b"hello",
        destination_path="firm1/case1/notice.pdf",
        content_type="application/pdf",
    )

    assert ref == "gs://test-bucket/firm1/case1/notice.pdf"
    blob = fake_client.bucket_obj.blobs["firm1/case1/notice.pdf"]
    assert blob.uploaded == (b"hello", "application/pdf")


def test_upload_document_raises_when_bucket_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.storage.get_settings", lambda: SimpleNamespace(cloud_storage_bucket=None)
    )

    with pytest.raises(RuntimeError):
        upload_document(file_bytes=b"x", destination_path="p", content_type="application/pdf")
