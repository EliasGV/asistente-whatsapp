from datetime import date
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.text_tools import build_custom_post


TOPICS = [
    {
        "title": "Datos municipales para decidir mejor",
        "angle": "Cómo las preguntas, reclamos y trámites repetidos pueden orientar prioridades reales de gestión local.",
    },
    {
        "title": "IA aplicada al municipalismo",
        "angle": "Usar IA para ordenar información, anticipar necesidades y mejorar la experiencia ciudadana sin perder criterio público.",
    },
    {
        "title": "Municipalismo de cercanía con evidencia",
        "angle": "La cercanía municipal se vuelve más potente cuando se combina con datos simples, oportunos y accionables.",
    },
    {
        "title": "Digitalización con trato humano",
        "angle": "Automatizar lo repetitivo para liberar tiempo, explicar mejor y derivar con responsabilidad.",
    },
    {
        "title": "Transparencia útil",
        "angle": "Pasar de publicar información a hacerla encontrable, comprensible y usable por vecinos y equipos municipales.",
    },
]


def build_linkedin_ideas(offset: int = 0) -> str:
    start = date(2026, 1, 1).toordinal()
    topic = TOPICS[(date.today().toordinal() - start + offset) % len(TOPICS)]

    draft = (
        f"Propuesta LinkedIn: {topic['title']}\n\n"
        f"Idea central: {topic['angle']}\n\n"
        "Borrador:\n"
        f"{_build_topic_draft(topic['title'])}"
    )

    return (
        "Mediodía: te dejo una propuesta de publicación sobre datos, IA y municipalismo.\n\n"
        f"{draft}\n\n"
        "Si te gusta, respóndeme: aprobar. Si quieres otra línea, respóndeme: otra idea."
    )


def build_linkedin_post(topic: str = "") -> str:
    return build_custom_post(topic)


def _build_topic_draft(title: str) -> str:
    drafts = {
        "Datos municipales para decidir mejor": (
            "Cada consulta repetida en un municipio es más que una molestia administrativa: es una señal.\n\n"
            "Si muchas personas preguntan lo mismo, quizás el trámite no está bien explicado. Si un reclamo se concentra "
            "en cierto sector, puede anticipar una prioridad territorial. Si un canal se satura, hay una oportunidad de rediseñar.\n\n"
            "Los datos municipales no siempre nacen en grandes tableros. Muchas veces aparecen en la atención diaria, "
            "en el mesón, en WhatsApp, en formularios y en conversaciones con vecinos.\n\n"
            "La pregunta no es solo cuántos datos tenemos, sino qué decisiones estamos tomando con ellos."
        ),
        "IA aplicada al municipalismo": (
            "La IA puede ser muy útil en gobiernos locales si parte por problemas concretos.\n\n"
            "Responder preguntas frecuentes, ordenar solicitudes, detectar patrones en reclamos o ayudar a escribir mejor "
            "información pública son usos simples, pero con impacto real en la experiencia ciudadana.\n\n"
            "El desafío no es reemplazar criterio municipal. Es liberar tiempo, reducir fricción y hacer que los equipos "
            "puedan concentrarse en casos que requieren contexto, empatía y decisión.\n\n"
            "La mejor IA pública no es la más vistosa: es la que vuelve más claro y oportuno el servicio."
        ),
        "Municipalismo de cercanía con evidencia": (
            "El municipalismo tiene una ventaja que ningún otro nivel del Estado posee con tanta intensidad: cercanía cotidiana.\n\n"
            "Esa cercanía permite ver problemas cuando todavía son señales pequeñas: una calle insegura, un trámite confuso, "
            "un servicio que llega tarde, una pregunta que se repite semana a semana.\n\n"
            "Pero la cercanía gana fuerza cuando se combina con evidencia. Escuchar mejor, medir lo necesario y actuar sobre "
            "patrones permite que la gestión local sea menos reactiva y más estratégica.\n\n"
            "Estar cerca importa. Aprender de lo que esa cercanía muestra importa todavía más."
        ),
        "Digitalización con trato humano": (
            "Digitalizar un municipio no debería significar alejarlo de las personas.\n\n"
            "Un buen canal digital explica, orienta y reduce pasos innecesarios. También reconoce cuando una persona necesita "
            "hablar con alguien, derivar bien o recibir una respuesta más cuidadosa.\n\n"
            "La tecnología sirve cuando baja la fricción: menos filas para lo simple, mejor información para decidir, "
            "y más tiempo humano para los casos complejos.\n\n"
            "Digitalizar con sentido público no es esconder el municipio detrás de una pantalla. Es hacerlo más accesible."
        ),
        "Transparencia útil": (
            "La transparencia no termina cuando la información se publica.\n\n"
            "Para que sea realmente útil, la información debe poder encontrarse, entenderse y usarse. Un PDF perdido, "
            "un dato sin contexto o una página difícil de navegar cumplen formalmente, pero ayudan poco.\n\n"
            "Los municipios tienen una oportunidad enorme: transformar información pública en herramientas simples para vecinos, "
            "organizaciones y equipos internos.\n\n"
            "La transparencia más valiosa no es la que solo exhibe datos. Es la que permite tomar mejores decisiones."
        ),
    }
    return drafts[title] + "\n\nPregunta para abrir conversación: ¿qué experiencia municipal concreta deberíamos mejorar con datos e IA?"


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
