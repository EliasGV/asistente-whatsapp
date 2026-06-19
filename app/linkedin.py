from datetime import date
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.text_tools import build_custom_post


TOPICS = [
    {
        "title": "Datos municipales para decidir mejor",
        "angle": "Como las preguntas, reclamos y tramites repetidos pueden orientar prioridades reales de gestion local.",
    },
    {
        "title": "IA aplicada al municipalismo",
        "angle": "Usar IA para ordenar informacion, anticipar necesidades y mejorar la experiencia ciudadana sin perder criterio publico.",
    },
    {
        "title": "Municipalismo de cercania con evidencia",
        "angle": "La cercania municipal se vuelve mas potente cuando se combina con datos simples, oportunos y accionables.",
    },
    {
        "title": "Digitalizacion con trato humano",
        "angle": "Automatizar lo repetitivo para liberar tiempo, explicar mejor y derivar con responsabilidad.",
    },
    {
        "title": "Transparencia util",
        "angle": "Pasar de publicar informacion a hacerla encontrable, comprensible y usable por vecinos y equipos municipales.",
    },
]


def build_linkedin_ideas() -> str:
    start = date(2026, 1, 1).toordinal()
    topic = TOPICS[(date.today().toordinal() - start) % len(TOPICS)]

    draft = (
        f"Propuesta LinkedIn: {topic['title']}\n\n"
        f"Idea central: {topic['angle']}\n\n"
        "Borrador:\n"
        "El municipalismo tiene una ventaja enorme: esta cerca de los problemas cotidianos. "
        "Esa cercania genera datos todos los dias: consultas, tiempos de respuesta, reclamos, "
        "tramites dificiles de entender y preguntas que se repiten.\n\n"
        "La IA puede ayudar a ordenar esas senales, pero el valor publico no esta solo en automatizar. "
        "Esta en convertir informacion dispersa en mejores decisiones, mejor comunicacion y servicios mas simples.\n\n"
        "Cuando un municipio escucha patrones y actua sobre ellos, la tecnologia deja de ser decoracion "
        "y se transforma en capacidad institucional.\n\n"
        "Pregunta para abrir conversacion: que dato municipal deberiamos mirar con mas atencion?"
    )

    return (
        "Mediodia: te dejo una propuesta de publicacion sobre datos, IA y municipalismo.\n\n"
        f"{draft}\n\n"
        "Si te gusta, respondeme: aprobar. Si quieres otra linea, respondeme: otra idea."
    )


def build_linkedin_post(topic: str = "") -> str:
    return build_custom_post(topic)


_runtime_access_token = ""
_runtime_person_urn = ""


def build_authorization_url(redirect_uri: str) -> str:
    if not settings.linkedin_client_id:
        raise RuntimeError("Missing LINKEDIN_CLIENT_ID.")

    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.linkedin_client_id,
            "redirect_uri": redirect_uri,
            "state": settings.linkedin_state_secret,
            "scope": "openid profile w_member_social",
        }
    )
    return f"https://www.linkedin.com/oauth/v2/authorization?{query}"


async def exchange_authorization_code(code: str, state: str | None, redirect_uri: str) -> dict[str, str]:
    if state != settings.linkedin_state_secret:
        raise RuntimeError("LinkedIn state mismatch.")
    if not settings.linkedin_client_id or not settings.linkedin_client_secret:
        raise RuntimeError("Missing LINKEDIN_CLIENT_ID or LINKEDIN_CLIENT_SECRET.")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        token_response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_response.raise_for_status()
        token_payload = token_response.json()
        access_token = token_payload["access_token"]

        person_urn = await _fetch_person_urn(client, access_token)

    global _runtime_access_token, _runtime_person_urn
    _runtime_access_token = access_token
    _runtime_person_urn = person_urn

    return {
        "access_token": access_token,
        "person_urn": person_urn,
        "expires_in": str(token_payload.get("expires_in", "")),
    }


async def _fetch_person_urn(client: httpx.AsyncClient, access_token: str) -> str:
    headers = {"Authorization": f"Bearer {access_token}"}

    userinfo = await client.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    if userinfo.status_code < 400:
        subject = userinfo.json().get("sub")
        if subject:
            return f"urn:li:person:{subject}"

    profile = await client.get("https://api.linkedin.com/v2/me", headers=headers)
    profile.raise_for_status()
    return f"urn:li:person:{profile.json()['id']}"


async def publish_text_post(text: str) -> str:
    access_token = _runtime_access_token or settings.linkedin_access_token
    person_urn = _runtime_person_urn or settings.linkedin_person_urn
    if not access_token or not person_urn:
        raise RuntimeError("LinkedIn is not connected. Open /linkedin/login first.")

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload)
        response.raise_for_status()
        return response.headers.get("x-restli-id", "publicado")
