import asyncio

from mangum import Mangum

from app.config import settings
from app.linkedin import build_linkedin_ideas
from app.main import app
from app.metro import build_morning_report
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

    return {"status": "unknown-task", "task": task}
