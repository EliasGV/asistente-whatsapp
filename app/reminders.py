import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings
from app.memory_store import put_item


WEEKDAYS = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "miércoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "sábado": 5,
    "domingo": 6,
}


def _next_weekday(target: int, hour: int, minute: int) -> datetime:
    tz = ZoneInfo(settings.timezone)
    now = datetime.now(tz)
    days = (target - now.weekday()) % 7
    run_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days)
    if run_at <= now:
        run_at += timedelta(days=7)
    return run_at


def _parse_time(text: str) -> tuple[int, int]:
    match = re.search(r"\b(\d{1,2})(?::|\.|h)?(\d{2})?\b", text)
    if not match:
        return 9, 0
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    return max(0, min(hour, 23)), max(0, min(minute, 59))


def parse_reminder_time(text: str) -> datetime:
    normalized = text.lower()
    hour, minute = _parse_time(normalized)
    tz = ZoneInfo(settings.timezone)
    now = datetime.now(tz)

    if "pasado mañana" in normalized or "pasado manana" in normalized:
        return (now + timedelta(days=2)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    if "mañana" in normalized or "manana" in normalized:
        return (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    for name, weekday in WEEKDAYS.items():
        if name in normalized:
            return _next_weekday(weekday, hour, minute)

    run_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if run_at <= now:
        run_at += timedelta(days=1)
    return run_at


def _schedule_name(user: str, run_at: datetime) -> str:
    safe_user = re.sub(r"[^A-Za-z0-9]", "", user)[-12:] or "user"
    stamp = run_at.strftime("%Y%m%d%H%M%S")
    return f"asistente-recordatorio-{safe_user}-{stamp}"


def create_real_reminder(user: str, text: str) -> str:
    if not text:
        return "Escríbeme el recordatorio después de `recordar`. Ejemplo: recordar llamar a Karina mañana 10:30."

    run_at = parse_reminder_time(text)
    item = put_item(user, "reminder", text, {"run_at": run_at.isoformat(), "status": "scheduled"})

    if not settings.reminder_scheduler_role_arn or not settings.reminder_lambda_arn:
        return (
            f"Recordatorio guardado para {run_at.strftime('%d-%m %H:%M')}. "
            "Para que avise solo falta configurar REMINDER_SCHEDULER_ROLE_ARN y REMINDER_LAMBDA_ARN."
        )

    boto3 = __import__("boto3")
    scheduler = boto3.client("scheduler")
    schedule_expression = f"at({run_at.strftime('%Y-%m-%dT%H:%M:%S')})"
    payload = {
        "task": "send-reminder",
        "secret": settings.task_secret,
        "to": user,
        "text": text,
        "memory_sk": item["sk"],
    }
    scheduler.create_schedule(
        Name=_schedule_name(user, run_at),
        ScheduleExpression=schedule_expression,
        ScheduleExpressionTimezone=settings.timezone,
        FlexibleTimeWindow={"Mode": "OFF"},
        Target={
            "Arn": settings.reminder_lambda_arn,
            "RoleArn": settings.reminder_scheduler_role_arn,
            "Input": __import__("json").dumps(payload),
        },
        ActionAfterCompletion="DELETE",
    )
    return f"Listo. Te recordaré: {text}\nFecha: {run_at.strftime('%d-%m-%Y %H:%M')}."
