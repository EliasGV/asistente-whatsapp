from app.faq import find_answer
from app.gmail_client import build_email_summary, build_pending_email_summary
from app.linkedin import build_linkedin_ideas, build_linkedin_post, publish_text_post
from app.metro import build_morning_report
from app.news import build_news_digest
from app.productivity import (
    add_agenda_item,
    add_note,
    add_reminder,
    build_agenda,
    build_daily_notes,
    build_eye_drops_status,
    build_reminders,
    build_work_checklist,
    record_eye_drops,
)
from app.text_tools import build_minute, build_post_variant
from app.vehicle_restriction import build_vehicle_restriction_report


_last_linkedin_drafts: dict[str, str] = {}
_linkedin_idea_offsets: dict[str, int] = {}


def _extract_post_body(draft: str) -> str:
    return draft.replace("Borrador LinkedIn:\n\n", "", 1).strip()


async def answer_message(text: str, from_number: str = "") -> str:
    normalized = text.lower().strip()

    if normalized.startswith("minuta"):
        return build_minute(text[6:].strip(" :-"))

    if normalized.startswith("nota"):
        return add_note(from_number, text[4:].strip(" :-"))

    if normalized in {"bitacora", "bitácora", "resumen de hoy"}:
        return build_daily_notes(from_number)

    if normalized in {"agenda", "agenda hoy"}:
        return build_agenda(from_number)

    if normalized.startswith("agenda "):
        return add_agenda_item(from_number, text[6:].strip(" :-"))

    if normalized.startswith("recordar"):
        return add_reminder(from_number, text[8:].strip(" :-"))

    if normalized in {"recordatorios", "pendientes manuales"}:
        return build_reminders(from_number)

    if normalized in {"checklist", "checklist laboral"}:
        return build_work_checklist()

    if normalized in {"correo", "resumen correo", "gmail"}:
        return await build_email_summary()

    if normalized in {"pendientes", "correos pendientes", "pendientes correo"}:
        return await build_pending_email_summary()

    if "gotas" in normalized and any(word in normalized for word in ["si", "sí", "no", "puestas", "puse"]):
        return record_eye_drops(from_number, text)

    if normalized in {"gotas", "estado gotas"}:
        return build_eye_drops_status(from_number)

    if normalized in {"mas tecnico", "más técnico", "mas tecnica", "más técnica"}:
        draft = build_post_variant(_last_linkedin_drafts.get(from_number, ""), "tecnico")
        _last_linkedin_drafts[from_number] = _extract_post_body(draft)
        return f"{draft}\n\nSi esta version te gusta, respondeme: publicar"

    if normalized in {"mas politico", "más político", "mas politica", "más política"}:
        draft = build_post_variant(_last_linkedin_drafts.get(from_number, ""), "politico")
        _last_linkedin_drafts[from_number] = _extract_post_body(draft)
        return f"{draft}\n\nSi esta version te gusta, respondeme: publicar"

    if normalized in {"mas breve", "más breve"}:
        draft = build_post_variant(_last_linkedin_drafts.get(from_number, ""), "breve")
        _last_linkedin_drafts[from_number] = _extract_post_body(draft)
        return f"{draft}\n\nSi esta version te gusta, respondeme: publicar"

    if normalized in {"con datos", "mas datos", "más datos"}:
        draft = build_post_variant(_last_linkedin_drafts.get(from_number, ""), "datos")
        _last_linkedin_drafts[from_number] = _extract_post_body(draft)
        return f"{draft}\n\nSi esta version te gusta, respondeme: publicar"

    if normalized.startswith("post"):
        draft = build_linkedin_post(text[4:].strip(" :-"))
        if from_number:
            _last_linkedin_drafts[from_number] = _extract_post_body(draft)
        return f"{draft}\n\nSi esta version te gusta, respondeme: publicar"

    if normalized.startswith("noticias") or normalized in {"news", "actualidad"}:
        return await build_news_digest()

    if any(word in normalized for word in ["restriccion", "restricción", "sello verde", "patente"]):
        return build_vehicle_restriction_report(text)

    if any(word in normalized for word in ["metro", "trafico", "movilidad", "viaje", "salir", "traslado"]):
        return await build_morning_report()

    if any(word in normalized for word in ["linkedin", "publicacion", "municipalismo", "otra idea"]):
        if "otra idea" in normalized and from_number:
            _linkedin_idea_offsets[from_number] = _linkedin_idea_offsets.get(from_number, 0) + 1
        elif from_number:
            _linkedin_idea_offsets[from_number] = 0

        draft = build_linkedin_ideas(_linkedin_idea_offsets.get(from_number, 0))
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
