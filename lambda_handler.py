import asyncio

from mangum import Mangum

from app.calendar_client import build_calendar_daily_summary
from app.config import settings
from app.daily_messages import (
    build_0800_briefing,
    build_daily_planning,
    build_email_digest,
    build_eye_drops_followup_message,
    build_eye_drops_reminder,
    build_municipal_radar,
    build_nightly_summary,
)
from app.linkedin import build_linkedin_ideas
from app.main import app
from app.metro import build_metro_service_report, build_morning_report
from app.transcribe_audio import collect_finished_audio_memories
from app.whatsapp import send_text_message


api_handler = Mangum(app)


def handler(event, context):
    task = event.get("task") if isinstance(event, dict) else None
    if task:
        return asyncio.run(handle_task(task, event))
    return api_handler(event, context)


async def handle_task(task: str, event: dict) -> dict[str, str]:
    if settings.task_secret and event.get("secret") != settings.task_secret:
        return {"status": "forbidden"}

    if task == "morning-report":
        await send_text_message(settings.personal_whatsapp_to, await build_morning_report())
        return {"status": "sent", "task": task}

    if task == "linkedin-ideas":
        await send_text_message(settings.personal_whatsapp_to, build_linkedin_ideas())
        return {"status": "sent", "task": task}

    if task == "0800-briefing":
        await send_text_message(settings.personal_whatsapp_to, await build_0800_briefing())
        return {"status": "sent", "task": task}

    if task == "eye-drops-morning":
        await send_text_message(settings.personal_whatsapp_to, build_eye_drops_reminder("morning"))
        return {"status": "sent", "task": task}

    if task == "eye-drops-morning-followup":
        message = build_eye_drops_followup_message(settings.personal_whatsapp_to, "morning")
        if message:
            await send_text_message(settings.personal_whatsapp_to, message)
            return {"status": "sent", "task": task}
        return {"status": "already-confirmed", "task": task}

    if task == "1830-metro":
        await send_text_message(settings.personal_whatsapp_to, await build_metro_service_report())
        return {"status": "sent", "task": task}

    if task == "eye-drops-night":
        await send_text_message(settings.personal_whatsapp_to, build_eye_drops_reminder("night"))
        return {"status": "sent", "task": task}

    if task == "eye-drops-night-followup":
        message = build_eye_drops_followup_message(settings.personal_whatsapp_to, "night")
        if message:
            await send_text_message(settings.personal_whatsapp_to, message)
            return {"status": "sent", "task": task}
        return {"status": "already-confirmed", "task": task}

    if task == "email-summary":
        await send_text_message(settings.personal_whatsapp_to, await build_email_digest())
        return {"status": "sent", "task": task}

    if task == "daily-planning":
        await send_text_message(settings.personal_whatsapp_to, await build_daily_planning())
        return {"status": "sent", "task": task}

    if task == "calendar-daily-summary":
        await send_text_message(settings.personal_whatsapp_to, await build_calendar_daily_summary())
        return {"status": "sent", "task": task}

    if task == "send-reminder":
        to = event.get("to") or settings.personal_whatsapp_to
        text = event.get("text", "")
        await send_text_message(to, f"Recordatorio: {text}")
        return {"status": "sent", "task": task}

    if task == "nightly-summary":
        await send_text_message(settings.personal_whatsapp_to, await build_nightly_summary(settings.personal_whatsapp_to))
        return {"status": "sent", "task": task}

    if task == "municipal-radar":
        await send_text_message(settings.personal_whatsapp_to, await build_municipal_radar())
        return {"status": "sent", "task": task}

    if task == "collect-audios":
        message = await collect_finished_audio_memories(settings.personal_whatsapp_to, silent=True)
        if message:
            await send_text_message(settings.personal_whatsapp_to, message)
            return {"status": "sent", "task": task}
        return {"status": "no-audios", "task": task}

    return {"status": "unknown-task", "task": task}
