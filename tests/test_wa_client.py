from types import SimpleNamespace

import pytest

from app.services.wa_client import send_whatsapp_message


def test_send_whatsapp_message_raises_when_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.wa_client.get_settings",
        lambda: SimpleNamespace(wa_phone_number_id=None, wa_access_token=None),
    )

    with pytest.raises(RuntimeError):
        send_whatsapp_message(to="+911234567890", body="hi")


def test_send_whatsapp_message_posts_and_returns_message_id(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.wa_client.get_settings",
        lambda: SimpleNamespace(wa_phone_number_id="123", wa_access_token="secret-token"),
    )

    captured = {}

    class _FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"messages": [{"id": "wamid.abc123"}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return _FakeResponse()

    monkeypatch.setattr("app.services.wa_client.httpx.post", fake_post)

    message_id = send_whatsapp_message(to="+911234567890", body="Reminder text")

    assert message_id == "wamid.abc123"
    assert captured["json"]["to"] == "+911234567890"
    assert captured["json"]["text"]["body"] == "Reminder text"
    assert "123" in captured["url"]
    assert captured["headers"]["Authorization"] == "Bearer secret-token"
