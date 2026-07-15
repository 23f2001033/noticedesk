import httpx

from app.config import get_settings

WHATSAPP_API_VERSION = "v20.0"


def send_whatsapp_message(*, to: str, body: str) -> str:
    """Sends a WhatsApp text message via the Business Cloud API, returns the
    provider message id.

    NOTE: not yet smoke-tested against live WhatsApp Business credentials --
    no WA_ACCESS_TOKEN provisioned yet (see PROGRESS.md).
    """
    settings = get_settings()
    if not settings.wa_phone_number_id or not settings.wa_access_token:
        raise RuntimeError("WA_PHONE_NUMBER_ID and WA_ACCESS_TOKEN must both be configured")

    url = (
        f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{settings.wa_phone_number_id}/messages"
    )
    response = httpx.post(
        url,
        headers={"Authorization": f"Bearer {settings.wa_access_token}"},
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()["messages"][0]["id"]
