from urllib.parse import urlencode

import httpx

from app.config import settings


GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_URL = "https://gmail.googleapis.com/gmail/v1/users/me"


def build_gmail_authorization_url(redirect_uri: str) -> str:
    if not settings.google_client_id:
        raise RuntimeError("Missing GOOGLE_CLIENT_ID.")

    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": GMAIL_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": settings.google_state_secret,
        }
    )
    return f"{GOOGLE_AUTH_URL}?{query}"


async def exchange_gmail_authorization_code(code: str, state: str | None, redirect_uri: str) -> dict[str, str]:
    if state != settings.google_state_secret:
        raise RuntimeError("Google state mismatch.")
    if not settings.google_client_id or not settings.google_client_secret:
        raise RuntimeError("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET.")

    data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        payload = response.json()

    return {
        "access_token": payload.get("access_token", ""),
        "refresh_token": payload.get("refresh_token", ""),
        "expires_in": str(payload.get("expires_in", "")),
        "scope": payload.get("scope", ""),
    }


async def _get_access_token() -> str:
    if settings.gmail_access_token and not settings.gmail_refresh_token:
        return settings.gmail_access_token
    if not settings.gmail_refresh_token:
        raise RuntimeError("Gmail is not connected. Open /gmail/login first.")

    data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "refresh_token": settings.gmail_refresh_token,
        "grant_type": "refresh_token",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json()["access_token"]


def _header(headers: list[dict[str, str]], name: str) -> str:
    for item in headers:
        if item.get("name", "").lower() == name.lower():
            return item.get("value", "")
    return ""


async def _fetch_messages(query: str, max_results: int = 8) -> list[dict[str, str]]:
    access_token = await _get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        list_response = await client.get(
            f"{GMAIL_API_URL}/messages",
            params={"q": query, "maxResults": max_results},
        )
        list_response.raise_for_status()
        ids = [item["id"] for item in list_response.json().get("messages", [])]

        messages = []
        for message_id in ids:
            message_response = await client.get(
                f"{GMAIL_API_URL}/messages/{message_id}",
                params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
            )
            message_response.raise_for_status()
            payload = message_response.json()
            metadata = payload.get("payload", {}).get("headers", [])
            messages.append(
                {
                    "from": _header(metadata, "From"),
                    "subject": _header(metadata, "Subject") or "(sin asunto)",
                    "date": _header(metadata, "Date"),
                    "snippet": payload.get("snippet", ""),
                }
            )
    return messages


def _format_messages(title: str, messages: list[dict[str, str]]) -> str:
    if not messages:
        return f"{title}\nNo encontre correos relevantes con ese criterio."

    lines = [title]
    for index, message in enumerate(messages, start=1):
        sender = message["from"].split("<", 1)[0].strip().strip('"') or message["from"]
        snippet = message["snippet"][:180]
        lines.append(f"{index}. {message['subject']}\n   De: {sender}\n   Pista: {snippet}")
    return "\n".join(lines)


async def build_email_summary() -> str:
    try:
        messages = await _fetch_messages("newer_than:2d -category:promotions -in:spam -in:trash", 8)
    except Exception as exc:
        return f"No pude leer Gmail todavia. Conecta la cuenta en /gmail/login. Detalle tecnico: {exc}"
    return _format_messages("Resumen Gmail: correos recientes relevantes", messages)


async def build_pending_email_summary() -> str:
    query = 'newer_than:7d -category:promotions -in:spam -in:trash ("?" OR responder OR pendiente OR urgente OR revisar OR confirmar)'
    try:
        messages = await _fetch_messages(query, 8)
    except Exception as exc:
        return f"No pude leer Gmail todavia. Conecta la cuenta en /gmail/login. Detalle tecnico: {exc}"
    return _format_messages("Pendientes Gmail: posibles correos que requieren accion", messages)
