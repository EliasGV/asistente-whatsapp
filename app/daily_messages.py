from app.gmail_client import build_email_summary, build_pending_email_summary
from app.metro import build_metro_service_report
from app.productivity import build_work_checklist
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
