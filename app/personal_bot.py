from app.faq import find_answer
from app.linkedin import build_linkedin_ideas
from app.metro import build_morning_report


async def answer_message(text: str) -> str:
    normalized = text.lower().strip()

    if any(word in normalized for word in ["metro", "tráfico", "trafico", "movilidad", "viaje"]):
        return await build_morning_report()

    if any(word in normalized for word in ["linkedin", "publicación", "publicacion", "post", "municipalismo", "otra idea"]):
        return build_linkedin_ideas()

    if normalized in {"aprobar", "aprobado", "ok publicar", "me gusta"}:
        return (
            "Perfecto. Queda aprobada como idea de publicación. "
            "Yo no la publico automáticamente en LinkedIn; te la dejo lista para revisar y publicar desde tu cuenta."
        )

    return find_answer(text)
