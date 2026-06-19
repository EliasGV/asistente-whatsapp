import asyncio

from mangum import Mangum

from app.config import settings
from app.daily_messages import build_0800_briefing, build_daily_planning, build_email_digest, build_eye_drops_reminder
from app.linkedin import build_linkedin_ideas
from app.main import app
from app.metro import build_metro_service_report, build_morning_report
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

    if task == "1830-metro":
        await send_text_message(settings.personal_whatsapp_to, await build_metro_service_report())
        return {"status": "sent", "task": task}

    if task == "eye-drops-night":
        await send_text_message(settings.personal_whatsapp_to, build_eye_drops_reminder("night"))
        return {"status": "sent", "task": task}

    if task == "email-summary":
        await send_text_message(settings.personal_whatsapp_to, await build_email_digest())
        return {"status": "sent", "task": task}

    if task == "daily-planning":
        await send_text_message(settings.personal_whatsapp_to, await build_daily_planning())
        return {"status": "sent", "task": task}

    return {"status": "unknown-task", "task": task}
