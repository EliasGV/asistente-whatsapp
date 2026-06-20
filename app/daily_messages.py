from app.gmail_client import build_email_summary, build_pending_email_summary
from app.metro import build_metro_service_report
from app.news import build_news_digest
from app.linkedin import build_linkedin_ideas
from app.productivity import build_agenda, build_daily_notes, build_eye_drops_status, build_reminders, build_work_checklist
from app.vehicle_restriction import build_vehicle_restriction_report
from app.weather_report import build_weather_report


async def build_0800_briefing() -> str:
    weather = await build_weather_report()
    restriction = build_vehicle_restriction_report()
    metro = await build_metro_service_report()
    return (
        "Buenos dias. Reporte 08:00\n\n"
        f"{weather}\n\n"
        f"{restriction}\n\n"
        f"{metro}"
    )


def build_eye_drops_reminder(period: str) -> str:
    if period == "morning":
        return "Recordatorio 09:00: te pusiste las gotas del glaucoma?"
    return "Recordatorio 21:00: te pusiste las gotas del glaucoma?"


async def build_email_digest() -> str:
    recent = await build_email_summary()
    pending = await build_pending_email_summary()
    return f"Resumen de correo:\n\n{recent}\n\n{pending}"


async def build_daily_planning() -> str:
    email = await build_pending_email_summary()
    return (
        "Planificacion rapida del dia:\n\n"
        f"{build_work_checklist()}\n\n"
        f"{email}"
    )


async def build_daily_mode(user: str) -> str:
    weather = await build_weather_report()
    metro = await build_metro_service_report()
    pending = await build_pending_email_summary()
    return (
        "Modo diario:\n\n"
        f"{weather}\n\n"
        f"{build_vehicle_restriction_report()}\n\n"
        f"{metro}\n\n"
        f"{build_agenda(user)}\n\n"
        f"{build_reminders(user)}\n\n"
        f"{build_eye_drops_status(user)}\n\n"
        f"{pending}"
    )


async def build_nightly_summary(user: str) -> str:
    return (
        "Cierre del día:\n\n"
        f"{build_daily_notes(user)}\n\n"
        f"{build_reminders(user)}\n\n"
        f"{build_eye_drops_status(user)}\n\n"
        "Pregunta breve: ¿hay algo de hoy que quieras guardar para terapia? Puedes responder: recuerdo <texto>."
    )


async def build_municipal_radar() -> str:
    news = await build_news_digest()
    idea = build_linkedin_ideas()
    return (
        "Radar municipal:\n\n"
        f"{news}\n\n"
        "Idea publicable:\n"
        f"{idea}"
    )
