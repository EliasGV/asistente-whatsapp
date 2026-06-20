from app.faq import find_answer
from app.gmail_client import build_email_summary, build_meeting_brief, build_pending_email_summary, build_reply_draft
from app.daily_messages import build_daily_mode, build_municipal_radar, build_nightly_summary
from app.linkedin import build_linkedin_ideas, build_linkedin_post, publish_text_post
from app.metro import build_morning_report
from app.news import build_news_digest
from app.productivity import (
    add_agenda_item,
    add_note,
    add_reminder,
    add_therapy_memory,
    build_agenda,
    build_daily_notes,
    build_eye_drops_status,
    build_reminders,
    build_therapy_summary,
    build_work_checklist,
    delete_memory,
    mark_commitment_done,
    record_eye_drops,
    search_memory,
)
from app.reminders import cancel_reminder, reschedule_reminder
from app.text_tools import build_minute, build_post_variant
from app.transcribe_audio import collect_finished_audio_memories
from app.vehicle_restriction import build_vehicle_restriction_report


_last_linkedin_drafts: dict[str, str] = {}
_linkedin_idea_offsets: dict[str, int] = {}


def _extract_post_body(draft: str) -> str:
    return draft.replace("Borrador LinkedIn:\n\n", "", 1).strip()


def build_extended_help() -> str:
    return (
        "Ayuda ampliada:\n\n"
        "Movilidad:\n"
        "- metro / salir: clima, restriccion vehicular y estado de Metro.\n"
        "- restriccion / restriccion manana: revisa tus autos configurados.\n\n"
        "Correo y trabajo:\n"
        "- correo: resumen ejecutivo del inbox reciente.\n"
        "- pendientes: correos priorizados por accion.\n"
        "- reunion <tema>: prepara contexto de reunion con correos relacionados.\n"
        "- responder correo <tema>: arma un borrador de respuesta sin enviarlo.\n"
        "- minuta <texto>: transforma notas en minuta ejecutiva.\n\n"
        "Memoria y recordatorios:\n"
        "- nota <texto>: guarda bitacora persistente.\n"
        "- bitacora: muestra notas recientes.\n"
        "- agenda <texto>: guarda un punto de agenda manual.\n"
        "- recordar <texto + fecha/hora>: crea un recordatorio real si EventBridge esta configurado.\n"
        "- recordar todos los dias <texto> 21:00: crea un recordatorio recurrente diario.\n"
        "- recordar cada lunes <texto> 08:30: crea un recordatorio semanal.\n"
        "- recordar lunes a viernes <texto> 08:15: crea un recordatorio de dias laborales.\n"
        "- recordatorios: lista recordatorios guardados.\n"
        "- cancelar <palabra clave>: cancela recordatorios.\n"
        "- cambiar recordatorio <clave> a mañana 12:00: cambia fecha/hora.\n"
        "- cumplido <palabra clave>: marca un pendiente como cumplido.\n\n"
        "Salud y terapia:\n"
        "- si / no / si gotas / no gotas: registra si te pusiste las gotas.\n"
        "- gotas: muestra registro.\n"
        "- recuerdo <texto>: guarda algo para terapia.\n"
        "- audios: revisa transcripciones listas y las guarda como recuerdos.\n"
        "- terapia: prepara resumen previo a sesion psicologica.\n\n"
        "LinkedIn:\n"
        "- linkedin / otra idea: genera ideas.\n"
        "- post <tema>: crea borrador.\n"
        "- mas tecnico / mas politico / mas breve / con datos: ajusta estilo.\n"
        "- publicar: publica el ultimo borrador aprobado."
    )


async def answer_message(text: str, from_number: str = "") -> str:
    normalized = text.lower().strip()

    if normalized in {"si", "sí", "sip", "sipo", "si me las puse", "sí me las puse"}:
        return record_eye_drops(from_number, "si gotas")

    if normalized in {"no", "nop", "no me las puse"}:
        return record_eye_drops(from_number, "no gotas")

    if normalized in {"ayuda mas", "ayuda más", "mas ayuda", "más ayuda"}:
        return build_extended_help()

    if normalized.startswith("minuta"):
        return build_minute(text[6:].strip(" :-"))

    if normalized.startswith("nota"):
        return add_note(from_number, text[4:].strip(" :-"))

    if normalized.startswith("recuerdo"):
        return add_therapy_memory(from_number, text[8:].strip(" :-"))

    if normalized in {"terapia", "resumen terapia", "memoria terapia"}:
        return build_therapy_summary(from_number)

    if normalized in {"diario", "modo diario"}:
        return await build_daily_mode(from_number)

    if normalized in {"cierre", "cierre dia", "cierre día", "resumen noche", "resumen nocturno"}:
        return await build_nightly_summary(from_number)

    if normalized in {"radar municipal", "radar", "radar municipios"}:
        return await build_municipal_radar()

    if normalized in {"audios", "audio", "transcripciones", "revisar audios"}:
        return await collect_finished_audio_memories(from_number)

    if normalized in {"bitacora", "bitácora", "resumen de hoy"}:
        return build_daily_notes(from_number)

    if normalized in {"agenda", "agenda hoy"}:
        return build_agenda(from_number)

    if normalized.startswith("agenda "):
        return add_agenda_item(from_number, text[6:].strip(" :-"))

    if normalized.startswith("recordar"):
        return add_reminder(from_number, text[8:].strip(" :-"))

    if normalized.startswith("cancelar"):
        return cancel_reminder(from_number, text[8:].strip(" :-"))

    if normalized.startswith("cambiar recordatorio"):
        return reschedule_reminder(from_number, text[len("cambiar recordatorio"):].strip(" :-"))

    if normalized.startswith("cumplido"):
        return mark_commitment_done(from_number, text[8:].strip(" :-"))

    if normalized in {"recordatorios", "pendientes manuales"}:
        return build_reminders(from_number)

    if normalized.startswith("buscar memoria") or normalized.startswith("que dije sobre") or normalized.startswith("qué dije sobre"):
        query = (
            text[len("buscar memoria"):].strip(" :-")
            if normalized.startswith("buscar memoria")
            else text.split("sobre", 1)[1].strip(" :-") if "sobre" in normalized else ""
        )
        return search_memory(from_number, query)

    if normalized.startswith("borrar memoria"):
        return delete_memory(from_number, text[len("borrar memoria"):].strip(" :-"))

    if normalized in {"checklist", "checklist laboral"}:
        return build_work_checklist()

    if normalized in {"correo", "resumen correo", "gmail"}:
        return await build_email_summary()

    if normalized in {"pendientes", "correos pendientes", "pendientes correo"}:
        return await build_pending_email_summary()

    if normalized.startswith("reunion") or normalized.startswith("reunión"):
        parts = text.split(maxsplit=1)
        return await build_meeting_brief(parts[1] if len(parts) > 1 else "")

    if normalized.startswith("responder correo"):
        return await build_reply_draft(text[len("responder correo"):].strip(" :-"))

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

    if any(word in normalized for word in ["metro", "trafico", "tráfico", "movilidad", "viaje", "salir", "traslado"]):
        return await build_morning_report()

    if any(word in normalized for word in ["linkedin", "publicacion", "publicación", "municipalismo", "otra idea"]):
        if "otra idea" in normalized and from_number:
            _linkedin_idea_offsets[from_number] = _linkedin_idea_offsets.get(from_number, 0) + 1
        elif from_number:
            _linkedin_idea_offsets[from_number] = 0

        draft = build_linkedin_ideas(_linkedin_idea_offsets.get(from_number, 0))
        if from_number:
            marker = "Borrador:\n"
            body = draft.split(marker, 1)[1].split("\n\nSi te gusta", 1)[0].strip() if marker in draft else draft
            _last_linkedin_drafts[from_number] = body
        return draft.replace("respóndeme: aprobar", "respóndeme: publicar")

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
