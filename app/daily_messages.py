from app.metro import build_metro_service_report
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
