from datetime import datetime, time
from zoneinfo import ZoneInfo

import httpx

from app.config import settings
from app.gmail_client import get_google_access_token


CALENDAR_API_URL = "https://www.googleapis.com/calendar/v3"


def _today_bounds() -> tuple[str, str]:
    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()
    start = datetime.combine(today, time.min, tzinfo=tz)
    end = datetime.combine(today, time.max, tzinfo=tz)
    return start.isoformat(), end.isoformat()


def _event_time(event: dict) -> str:
    start = event.get("start", {})
    end = event.get("end", {})
    if "date" in start:
        return "todo el dia"

    tz = ZoneInfo(settings.timezone)
    try:
        start_dt = datetime.fromisoformat(start.get("dateTime", "").replace("Z", "+00:00")).astimezone(tz)
        end_dt = datetime.fromisoformat(end.get("dateTime", "").replace("Z", "+00:00")).astimezone(tz)
        return f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
    except Exception:
        return "hora no disponible"


def _event_place(event: dict) -> str:
    location = (event.get("location") or "").strip()
    hangout = (event.get("hangoutLink") or "").strip()
    if location:
        return location
    if hangout:
        return "videollamada"
    return ""


async def fetch_today_events(max_results: int = 12) -> list[dict]:
    access_token = await get_google_access_token()
    time_min, time_max = _today_bounds()
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": max_results,
    }

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        response = await client.get(f"{CALENDAR_API_URL}/calendars/primary/events", params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Google Calendar API {response.status_code}: {response.text[:1000]}"
            ) from exc
        return response.json().get("items", [])


async def build_calendar_daily_summary() -> str:
    try:
        events = await fetch_today_events()
    except Exception as exc:
        return (
            "No pude leer Google Calendar todavia. "
            "Habilita Google Calendar API y vuelve a conectar Google en /gmail/login. "
            f"Detalle tecnico: {exc}"
        )

    if not events:
        return (
            "Agenda Google de hoy 07:30:\n"
            "No veo eventos en tu calendario principal para hoy.\n\n"
            "Sugerencia: define 1 prioridad principal antes de abrir el correo."
        )

    lines = ["Agenda Google de hoy 07:30:"]
    for index, event in enumerate(events, start=1):
        title = event.get("summary") or "(sin titulo)"
        place = _event_place(event)
        place_text = f" | {place}" if place else ""
        lines.append(f"{index}. {_event_time(event)} - {title}{place_text}")

    lines.append("\nSugerencia: antes de la primera reunion, revisa que cada bloque tenga objetivo y siguiente paso.")
    return "\n".join(lines)
