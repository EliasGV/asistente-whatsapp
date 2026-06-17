import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings
from app.linkedin import build_linkedin_ideas
from app.metro import build_morning_report
from app.whatsapp import send_text_message


def _next_run_at(time_text: str) -> datetime:
    hour, minute = [int(part) for part in time_text.split(":", maxsplit=1)]
    tz = ZoneInfo(settings.timezone)
    now = datetime.now(tz)
    run_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if run_at <= now:
        run_at += timedelta(days=1)
    return run_at


async def _daily_loop(time_text: str, builder) -> None:
    while True:
        run_at = _next_run_at(time_text)
        await asyncio.sleep((run_at - datetime.now(ZoneInfo(settings.timezone))).total_seconds())
        if settings.personal_whatsapp_to:
            message = await builder() if asyncio.iscoroutinefunction(builder) else builder()
            await send_text_message(settings.personal_whatsapp_to, message)


async def start_scheduler() -> None:
    if not settings.enable_scheduler:
        return
    asyncio.create_task(_daily_loop(settings.morning_report_time, build_morning_report))
    asyncio.create_task(_daily_loop(settings.linkedin_ideas_time, build_linkedin_ideas))
