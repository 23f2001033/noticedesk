from datetime import UTC, datetime

from app.models.case import Case, CaseSource, CaseStatus, NoticeType


def test_create_case_requires_auth(client) -> None:
    response = client.post(
        "/api/cases",
        data={"client_id": "client-1"},
        files={"file": ("notice.pdf", b"pdf bytes", "application/pdf")},
    )

    assert response.status_code == 401


def test_create_case_returns_case_on_success(monkeypatch, client, fake_firestore_with_user) -> None:
    monkeypatch.setattr("app.deps.verify_firebase_token", lambda token: {"uid": "uid-1"})
    monkeypatch.setattr(
        "app.deps.get_firestore_client",
        lambda: fake_firestore_with_user({"firm_id": "firm-1", "role": "partner"}),
    )

    fake_case = Case(
        firm_id="firm-1",
        client_id="client-1",
        notice_type=NoticeType.ASMT_10,
        status=CaseStatus.NEW,
        source=CaseSource.WEB,
        created_at=datetime.now(UTC),
    )
    monkeypatch.setattr("app.routers.cases.ingest_notice", lambda **kwargs: fake_case)

    response = client.post(
        "/api/cases",
        headers={"Authorization": "Bearer good-token"},
        data={"client_id": "client-1"},
        files={"file": ("notice.pdf", b"pdf bytes", "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["firm_id"] == "firm-1"
    assert body["notice_type"] == "ASMT-10"
