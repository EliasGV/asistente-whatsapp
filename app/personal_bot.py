from app.faq import find_answer
from app.linkedin import build_linkedin_ideas, build_linkedin_post
from app.metro import build_morning_report
from app.news import build_news_digest
from app.text_tools import build_minute


async def answer_message(text: str) -> str:
    normalized = text.lower().strip()

    if normalized.startswith("minuta"):
        return build_minute(text[6:].strip(" :-"))

    if normalized.startswith("post"):
        return build_linkedin_post(text[4:].strip(" :-"))

    if normalized.startswith("noticias") or normalized in {"news", "actualidad"}:
        return await build_news_digest()

    if any(word in normalized for word in ["metro", "trafico", "movilidad", "viaje"]):
        return await build_morning_report()

    if any(word in normalized for word in ["linkedin", "publicacion", "municipalismo", "otra idea"]):
        return build_linkedin_ideas()

    if normalized in {"aprobar", "aprobado", "ok publicar", "me gusta"}:
        return (
            "Perfecto. Queda aprobada como idea de publicacion. "
            "Yo no la publico automaticamente en LinkedIn; te la dejo lista para revisar y publicar desde tu cuenta."
        )

    return find_answer(text)
