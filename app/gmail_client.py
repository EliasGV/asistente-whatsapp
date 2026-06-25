import base64
import html
import re
from urllib.parse import urlencode

import httpx

from app.config import settings


GOOGLE_SCOPES = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar.readonly"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_URL = "https://gmail.googleapis.com/gmail/v1/users/me"
ACTION_WORDS = [
    "solicitud",
    "solicito",
    "solicitamos",
    "requiere",
    "requiero",
    "pendiente",
    "pendientes",
    "urgente",
    "plazo",
    "responder",
    "respuesta",
    "revisar",
    "validar",
    "confirmar",
    "remitir",
    "informe",
    "borrador",
    "workflow",
    "licitacion",
    "licitación",
    "presupuesto",
    "traspaso",
    "metrogas",
]
LOW_VALUE_WORDS = [
    "newsletter",
    "boletin",
    "boletín",
    "temas publicos",
    "temas públicos",
    "unsubscribe",
    "desuscribir",
    "publicidad",
]


def build_gmail_authorization_url(redirect_uri: str) -> str:
    if not settings.google_client_id:
        raise RuntimeError("Missing GOOGLE_CLIENT_ID.")

    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": GOOGLE_SCOPES,
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


async def get_google_access_token() -> str:
    return await _get_access_token()


def _clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>|</div>|</li>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _decode_body(data: str | None) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="ignore")


def _message_text(part: dict) -> str:
    mime_type = part.get("mimeType", "")
    body_data = part.get("body", {}).get("data")
    if body_data and mime_type in {"text/plain", "text/html"}:
        return _clean_text(_decode_body(body_data))

    pieces = []
    for child in part.get("parts", []) or []:
        child_text = _message_text(child)
        if child_text:
            pieces.append(child_text)
    return "\n".join(pieces)


def _header(headers: list[dict[str, str]], name: str) -> str:
    for item in headers:
        if item.get("name", "").lower() == name.lower():
            return item.get("value", "")
    return ""


def _sender_name(sender: str) -> str:
    return sender.split("<", 1)[0].strip().strip('"') or sender


def _sentences(text: str) -> list[str]:
    text = _clean_text(text)
    pieces = re.split(r"(?<=[.!?])\s+", text)
    return [piece.strip() for piece in pieces if 35 <= len(piece.strip()) <= 260]


def _score_message(message: dict[str, str]) -> int:
    haystack = f"{message['subject']} {message['from']} {message['body']}".lower()
    score = 0
    for word in ACTION_WORDS:
        if word in haystack:
            score += 3
    for word in LOW_VALUE_WORDS:
        if word in haystack:
            score -= 7
    if "no-reply" in message["from"].lower() and "workflow" not in haystack:
        score -= 3
    if "?" in message["body"] or "?" in message["subject"]:
        score += 2
    if any(word in haystack for word in ["jefe", "director", "secpla", "municipal", "presupuesto"]):
        score += 2
    return score


def _action_summary(message: dict[str, str]) -> str:
    subject = message["subject"]
    body = message["body"] or message["snippet"]
    lowered = f"{subject} {body}".lower()
    sentences = _sentences(body)

    if "workflow" in lowered:
        return "Accion sugerida: entrar a Workflow y revisar/aprobar la solicitud."
    if "presupuesto" in lowered:
        return "Accion sugerida: revisar antecedentes y preparar respuesta para el proceso presupuestario."
    if "traspaso" in lowered or "informe" in lowered:
        return "Accion sugerida: leer el informe y definir si requiere derivacion, comentarios o seguimiento."
    if "licitacion" in lowered or "licitación" in lowered or "eett" in lowered:
        return "Accion sugerida: revisar el borrador tecnico y validar observaciones antes de avanzar."
    if "metrogas" in lowered or "pendiente" in lowered:
        return "Accion sugerida: responder o derivar seguimiento de los puntos pendientes."
    if "adjunto" in lowered or "remito" in lowered:
        return "Accion sugerida: revisar el adjunto y confirmar recepcion o comentarios."
    if sentences:
        return f"Resumen: {sentences[0]}"
    return f"Resumen: {(body or subject)[:220].strip()}"


def _importance_reason(message: dict[str, str]) -> str:
    text = f"{message['subject']} {message['body']}".lower()
    reasons = []
    if any(word in text for word in ["urgente", "plazo", "presupuesto", "licitacion", "licitación"]):
        reasons.append("tiene plazo o impacto de gestion")
    if any(word in text for word in ["solicitud", "workflow", "requiere", "pendiente", "confirmar", "revisar"]):
        reasons.append("pide una accion concreta")
    if any(word in text for word in ["informe", "borrador", "adjunto", "remito"]):
        reasons.append("trae documento o antecedente para revisar")
    if not reasons:
        reasons.append("parece relevante por tema o remitente")
    return ", ".join(reasons[:2])


async def _fetch_messages(query: str, max_results: int = 15) -> list[dict[str, str]]:
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
                params={"format": "full"},
            )
            message_response.raise_for_status()
            payload = message_response.json()
            metadata = payload.get("payload", {}).get("headers", [])
            body = _message_text(payload.get("payload", {}))
            messages.append(
                {
                    "id": payload.get("id", ""),
                    "thread_id": payload.get("threadId", ""),
                    "from": _header(metadata, "From"),
                    "subject": _header(metadata, "Subject") or "(sin asunto)",
                    "date": _header(metadata, "Date"),
                    "snippet": payload.get("snippet", ""),
                    "body": body,
                }
            )
    return messages


def _dedupe_threads(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for message in messages:
        key = message.get("thread_id") or message.get("id") or message["subject"]
        if key in seen:
            continue
        seen.add(key)
        result.append(message)
    return result


def _rank_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(_dedupe_threads(messages), key=_score_message, reverse=True)


def _format_messages(title: str, messages: list[dict[str, str]], limit: int = 6) -> str:
    if not messages:
        return f"{title}\nNo encontre correos relevantes con ese criterio."

    lines = [title]
    for index, message in enumerate(_rank_messages(messages)[:limit], start=1):
        sender = _sender_name(message["from"])
        lines.append(
            f"{index}. {message['subject']}\n"
            f"   De: {sender}\n"
            f"   Por que importa: {_importance_reason(message)}.\n"
            f"   {_action_summary(message)}"
        )
    return "\n".join(lines)


def _short_summary(message: dict[str, str]) -> str:
    body = message["body"] or message["snippet"]
    sentences = _sentences(body)
    if sentences:
        summary = sentences[0]
    else:
        summary = (body or message["subject"])[:180].strip()
    return summary[:220].rstrip()


def _format_compact_item(message: dict[str, str]) -> str:
    sender = _sender_name(message["from"])
    return f"- {message['subject']} ({sender}): {_short_summary(message)}"


def _is_low_value(message: dict[str, str]) -> bool:
    haystack = f"{message['subject']} {message['from']} {message['body']}".lower()
    return any(word in haystack for word in LOW_VALUE_WORDS)


def _format_inbox_overview(messages: list[dict[str, str]]) -> str:
    messages = _rank_messages(messages)
    action = [message for message in messages if _score_message(message) >= 8 and not _is_low_value(message)]
    reading = [
        message for message in messages
        if 0 <= _score_message(message) < 8 and not _is_low_value(message)
    ]
    informational = [message for message in messages if _is_low_value(message) or _score_message(message) < 0]

    lines = ["Resumen Gmail: mirada ejecutiva del inbox reciente"]
    lines.append(f"Revise {len(messages)} hilos recientes. Prioridad alta: {len(action)}.")

    if action:
        lines.append("\nRequieren accion:")
        lines.extend(_format_compact_item(message) for message in action[:4])
    else:
        lines.append("\nRequieren accion:\n- No detecte acciones claras entre los correos recientes.")

    if reading:
        lines.append("\nPara leer/revisar:")
        lines.extend(_format_compact_item(message) for message in reading[:3])

    if informational:
        lines.append("\nInformativo o baja prioridad:")
        lines.extend(_format_compact_item(message) for message in informational[:2])

    lines.append("\nPara ver solo accionables, escribeme: pendientes.")
    return "\n".join(lines)


async def build_email_summary() -> str:
    try:
        messages = await _fetch_messages("newer_than:2d -category:social -in:spam -in:trash", 18)
    except Exception as exc:
        return f"No pude leer Gmail todavia. Conecta la cuenta en /gmail/login. Detalle tecnico: {exc}"
    return _format_inbox_overview(messages)


async def build_pending_email_summary() -> str:
    query = "newer_than:7d -category:promotions -category:social -in:spam -in:trash"
    try:
        messages = await _fetch_messages(query, 20)
    except Exception as exc:
        return f"No pude leer Gmail todavia. Conecta la cuenta en /gmail/login. Detalle tecnico: {exc}"
    ranked = [message for message in _rank_messages(messages) if _score_message(message) > 0]
    return _format_messages("Pendientes Gmail: correos priorizados por accion", ranked or messages, limit=6)


async def build_meeting_brief(topic: str) -> str:
    topic = (topic or "").strip()
    if not topic:
        return "Escríbeme el tema después de `reunion`. Ejemplo: reunion presupuesto salud."
    query = f'newer_than:30d -in:spam -in:trash "{topic}"'
    try:
        messages = await _fetch_messages(query, 10)
    except Exception as exc:
        return f"No pude preparar la reunión desde Gmail. Detalle técnico: {exc}"
    if not messages:
        return f"No encontré correos recientes sobre: {topic}."

    ranked = _rank_messages(messages)[:5]
    lines = [f"Modo reunión: {topic}", "", "Contexto desde Gmail:"]
    for message in ranked:
        lines.append(f"- {message['subject']} ({_sender_name(message['from'])}): {_short_summary(message)}")
    lines.append(
        "\nPreguntas sugeridas:\n"
        "- ¿Cuál es la decisión que debe salir de esta reunión?\n"
        "- ¿Qué antecedentes faltan?\n"
        "- ¿Quién queda responsable y con qué plazo?\n"
        "- ¿Qué riesgo conviene dejar explicitado?"
    )
    lines.append("\nDespués puedes escribirme: minuta <notas de la reunión>.")
    return "\n".join(lines)


async def build_reply_draft(topic: str) -> str:
    topic = (topic or "").strip()
    if not topic:
        return "Escríbeme el tema después de `responder correo`. Ejemplo: responder correo presupuesto salud."
    query = f'newer_than:30d -in:spam -in:trash "{topic}"'
    try:
        messages = await _fetch_messages(query, 5)
    except Exception as exc:
        return f"No pude buscar el correo para preparar respuesta. Detalle técnico: {exc}"
    if not messages:
        return f"No encontré correos recientes sobre: {topic}."

    message = _rank_messages(messages)[0]
    sender = _sender_name(message["from"])
    summary = _short_summary(message)
    return (
        f"Borrador de respuesta para: {message['subject']}\n"
        f"De: {sender}\n\n"
        "Estimado/a,\n\n"
        "Junto con saludar, gracias por el envío de los antecedentes.\n\n"
        f"Según lo revisado, entiendo que el punto principal es: {summary}\n\n"
        "Voy a revisar la información y coordinar los antecedentes necesarios para dar respuesta o derivar según corresponda. "
        "En caso de requerir algún insumo adicional, lo informaré oportunamente.\n\n"
        "Saludos cordiales."
    )
