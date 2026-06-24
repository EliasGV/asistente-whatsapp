import httpx

from app.config import settings


GRAPH_API_VERSION = "v22.0"


async def send_text_message(to: str, body: str) -> None:
    if not settings.whatsapp_token or not settings.whatsapp_phone_number_id:
        raise RuntimeError("Missing WhatsApp credentials. Check WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID.")

    url = (
        f"https://graph.facebook.com/{GRAPH_API_VERSION}/"
        f"{settings.whatsapp_phone_number_id}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, headers=headers, json=payload)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"WhatsApp API error {response.status_code}: {response.text[:1000]}"
            ) from exc
