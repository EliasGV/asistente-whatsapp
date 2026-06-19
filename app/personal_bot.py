from app.faq import find_answer
from app.linkedin import build_linkedin_ideas, build_linkedin_post, publish_text_post
from app.metro import build_morning_report
from app.news import build_news_digest
from app.text_tools import build_minute
from app.vehicle_restriction import build_vehicle_restriction_report


_last_linkedin_drafts: dict[str, str] = {}


def _extract_post_body(draft: str) -> str:
    return draft.replace("Borrador LinkedIn:\n\n", "", 1).strip()


async def answer_message(text: str, from_number: str = "") -> str:
    normalized = text.lower().strip()

    if normalized.startswith("minuta"):
        return build_minute(text[6:].strip(" :-"))

    if normalized.startswith("post"):
        draft = build_linkedin_post(text[4:].strip(" :-"))
        if from_number:
            _last_linkedin_drafts[from_number] = _extract_post_body(draft)
        return f"{draft}\n\nSi esta version te gusta, respondeme: publicar"

    if normalized.startswith("noticias") or normalized in {"news", "actualidad"}:
        return await build_news_digest()

    if any(word in normalized for word in ["restriccion", "restricción", "sello verde", "patente"]):
        return build_vehicle_restriction_report(text)

    if any(word in normalized for word in ["metro", "trafico", "movilidad", "viaje"]):
        return await build_morning_report()

    if any(word in normalized for word in ["linkedin", "publicacion", "municipalismo", "otra idea"]):
        draft = build_linkedin_ideas()
        if from_number:
            marker = "Borrador:\n"
            body = draft.split(marker, 1)[1].split("\n\nSi te gusta", 1)[0].strip() if marker in draft else draft
            _last_linkedin_drafts[from_number] = body
        return draft.replace("respondeme: aprobar", "respondeme: publicar")

    if normalized in {"publicar", "aprobar", "aprobado", "ok publicar", "me gusta"}:
        draft = _last_linkedin_drafts.get(from_number)
        if not draft:
            return "Todavia no tengo un borrador listo. Escribeme: post <tema>, o: linkedin."
        try:
            post_id = await publish_text_post(draft)
        except Exception as exc:
            return (
                "Aun no pude publicar en LinkedIn. "
                "Primero conecta la cuenta abriendo /linkedin/login en la URL del bot. "
                f"Detalle tecnico: {exc}"
            )
        return f"Publicado en LinkedIn. ID: {post_id}"

    return find_answer(text)
