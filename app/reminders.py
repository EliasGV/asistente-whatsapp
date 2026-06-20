import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings
from app.memory_store import delete_matching_items, list_items, put_item


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
AWS_WEEKDAYS = {
    0: "MON",
    1: "TUE",
    2: "WED",
    3: "THU",
    4: "FRI",
    5: "SAT",
    6: "SUN",
}


def _parse_time(text: str) -> tuple[int, int]:
    match = re.search(r"\b(\d{1,2})(?::|\.|h)?(\d{2})?\b", text)
    if not match:
        return 9, 0
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    return max(0, min(hour, 23)), max(0, min(minute, 59))


def _next_weekday(target: int, hour: int, minute: int) -> datetime:
    tz = ZoneInfo(settings.timezone)
    now = datetime.now(tz)
    days = (target - now.weekday()) % 7
    run_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days)
    if run_at <= now:
        run_at += timedelta(days=7)
    return run_at


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


def _recurrence_expression(text: str) -> tuple[str, str] | None:
    normalized = text.lower()
    hour, minute = _parse_time(normalized)

    if any(phrase in normalized for phrase in ["todos los dias", "todos los días", "cada dia", "cada día", "diario", "diariamente"]):
        return f"cron({minute} {hour} * * ? *)", f"todos los días a las {hour:02d}:{minute:02d}"

    if "lunes a viernes" in normalized or "de lunes a viernes" in normalized:
        return f"cron({minute} {hour} ? * MON-FRI *)", f"lunes a viernes a las {hour:02d}:{minute:02d}"

    for name, weekday in WEEKDAYS.items():
        if f"cada {name}" in normalized or f"todos los {name}" in normalized:
            aws_day = AWS_WEEKDAYS[weekday]
            return f"cron({minute} {hour} ? * {aws_day} *)", f"cada {name} a las {hour:02d}:{minute:02d}"

    return None


def _schedule_name(user: str, stamp: str) -> str:
    safe_user = re.sub(r"[^A-Za-z0-9]", "", user)[-12:] or "user"
    return f"asistente-recordatorio-{safe_user}-{stamp}"


def _create_schedule(name: str, expression: str, user: str, text: str, memory_sk: str, recurring: bool) -> None:
    boto3 = __import__("boto3")
    scheduler = boto3.client("scheduler")
    kwargs = {
        "Name": name,
        "ScheduleExpression": expression,
        "ScheduleExpressionTimezone": settings.timezone,
        "FlexibleTimeWindow": {"Mode": "OFF"},
        "Target": {
            "Arn": settings.reminder_lambda_arn,
            "RoleArn": settings.reminder_scheduler_role_arn,
            "Input": json.dumps(
                {
                    "task": "send-reminder",
                    "secret": settings.task_secret,
                    "to": user,
                    "text": text,
                    "memory_sk": memory_sk,
                    "recurring": recurring,
                }
            ),
        },
    }
    if not recurring:
        kwargs["ActionAfterCompletion"] = "DELETE"
    scheduler.create_schedule(**kwargs)


def create_real_reminder(user: str, text: str) -> str:
    if not text:
        return (
            "Escribeme el recordatorio despues de `recordar`.\n"
            "Ejemplos:\n"
            "- recordar llamar a Karina mañana 10:30\n"
            "- recordar todos los dias gotas 21:00\n"
            "- recordar cada lunes revisar planificación 08:30"
        )

    recurrence = _recurrence_expression(text)
    if recurrence:
        expression, label = recurrence
        stamp = datetime.now(ZoneInfo(settings.timezone)).strftime("%Y%m%d%H%M%S")
        schedule_name = _schedule_name(user, stamp)
        item = put_item(
            user,
            "reminder",
            text,
            {
                "schedule_name": schedule_name,
                "schedule_expression": expression,
                "recurrence": label,
                "status": "scheduled",
            },
        )
        if not settings.reminder_scheduler_role_arn or not settings.reminder_lambda_arn:
            return (
                f"Recordatorio recurrente guardado ({label}). "
                "Para que avise solo falta configurar REMINDER_SCHEDULER_ROLE_ARN y REMINDER_LAMBDA_ARN."
            )
        try:
            _create_schedule(schedule_name, expression, user, text, item["sk"], recurring=True)
        except Exception as exc:
            return (
                f"Guardé el recordatorio recurrente ({label}), pero no pude crear la alarma en EventBridge. "
                f"Detalle técnico: {exc}"
            )
        return f"Listo. Te recordaré {label}: {text}"

    run_at = parse_reminder_time(text)
    stamp = run_at.strftime("%Y%m%d%H%M%S")
    schedule_name = _schedule_name(user, stamp)
    item = put_item(
        user,
        "reminder",
        text,
        {
            "run_at": run_at.isoformat(),
            "schedule_name": schedule_name,
            "status": "scheduled",
        },
    )

    if not settings.reminder_scheduler_role_arn or not settings.reminder_lambda_arn:
        return (
            f"Recordatorio guardado para {run_at.strftime('%d-%m %H:%M')}. "
            "Para que avise solo falta configurar REMINDER_SCHEDULER_ROLE_ARN y REMINDER_LAMBDA_ARN."
        )

    try:
        _create_schedule(
            schedule_name,
            f"at({run_at.strftime('%Y-%m-%dT%H:%M:%S')})",
            user,
            text,
            item["sk"],
            recurring=False,
        )
    except Exception as exc:
        return (
            f"Guardé el recordatorio para {run_at.strftime('%d-%m %H:%M')}, "
            f"pero no pude crear la alarma en EventBridge. Detalle técnico: {exc}"
        )

    return f"Listo. Te recordaré: {text}\nFecha: {run_at.strftime('%d-%m-%Y %H:%M')}."


def _delete_schedule(schedule_name: str) -> None:
    if not schedule_name:
        return
    boto3 = __import__("boto3")
    scheduler = boto3.client("scheduler")
    scheduler.delete_schedule(Name=schedule_name)


def cancel_reminder(user: str, text: str) -> str:
    needle = text.lower().strip()
    if not needle:
        return "Escríbeme qué recordatorio quieres cancelar. Ejemplo: cancelar Karina."

    matches = [
        item for item in list_items(user, "reminder", limit=50)
        if needle in item.get("text", "").lower()
    ]
    if not matches:
        return "No encontré un recordatorio parecido."

    deleted_schedules = 0
    for item in matches:
        try:
            _delete_schedule(item.get("schedule_name", ""))
            deleted_schedules += 1
        except Exception as exc:
            print(f"Could not delete schedule: {exc}")

    deleted_items = delete_matching_items(user, "reminder", text)
    return f"Cancelé {deleted_items} recordatorio(s). Schedules eliminados: {deleted_schedules}."


def reschedule_reminder(user: str, text: str) -> str:
    normalized = text.strip()
    if " a " not in normalized.lower():
        return "Usa este formato: cambiar recordatorio <palabra clave> a mañana 12:00."

    before, after = re.split(r"\s+a\s+", normalized, maxsplit=1, flags=re.I)
    keyword = before.strip()
    matches = [
        item for item in list_items(user, "reminder", limit=50)
        if keyword.lower() in item.get("text", "").lower()
    ]
    if not matches:
        return "No encontré un recordatorio parecido para cambiar."

    original = matches[-1]["text"]
    cancel_reminder(user, keyword)
    return create_real_reminder(user, f"{original} {after}")
