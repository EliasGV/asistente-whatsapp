from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings


RESTRICTION_START_MONTH = 5
RESTRICTION_END_MONTH = 8
RESTRICTION_START_HOUR = "07:30"
RESTRICTION_END_HOUR = "21:00"
GREEN_PRE_2011_SCHEDULE = {
    0: {"8", "9"},
    1: {"0", "1"},
    2: {"2", "3"},
    3: {"4", "5"},
    4: {"6", "7"},
}


def _today() -> date:
    return datetime.now(ZoneInfo(settings.timezone)).date()


def _parse_query_date(text: str) -> date:
    normalized = text.lower()
    current = _today()
    if "manana" in normalized or "mañana" in normalized:
        return current + timedelta(days=1)
    return current


def _in_restriction_season(day: date) -> bool:
    return RESTRICTION_START_MONTH <= day.month <= RESTRICTION_END_MONTH


def _vehicle_is_old_green(year: int) -> bool:
    return year < 2012


def _is_restricted(day: date, year: int, digit: str) -> bool:
    if not _in_restriction_season(day):
        return False
    if day.weekday() not in GREEN_PRE_2011_SCHEDULE:
        return False
    if not _vehicle_is_old_green(year):
        return False
    return digit in GREEN_PRE_2011_SCHEDULE[day.weekday()]


def _format_day(day: date) -> str:
    names = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    return f"{names[day.weekday()]} {day.strftime('%d-%m-%Y')}"


def build_vehicle_restriction_report(text: str = "") -> str:
    day = _parse_query_date(text)
    vehicles = [
        {
            "name": "Auto sello verde previo a 2011",
            "year": settings.vehicle_one_year,
            "digit": settings.vehicle_one_digit,
        },
        {
            "name": "Auto sello verde 2019",
            "year": settings.vehicle_two_year,
            "digit": settings.vehicle_two_digit,
        },
    ]

    lines = [f"Restriccion vehicular para {_format_day(day)}:"]

    if not _in_restriction_season(day):
        lines.append("Fuera del periodo normal mayo-agosto: no aplica restriccion normal de invierno.")
    elif day.weekday() >= 5:
        lines.append("Es fin de semana: no aplica restriccion normal de lunes a viernes.")
    else:
        digits = ", ".join(sorted(GREEN_PRE_2011_SCHEDULE[day.weekday()]))
        lines.append(
            f"Horario normal: {RESTRICTION_START_HOUR} a {RESTRICTION_END_HOUR}. "
            f"Digitos restringidos para sello verde antiguo: {digits}."
        )

    for vehicle in vehicles:
        restricted = _is_restricted(day, vehicle["year"], vehicle["digit"])
        if restricted:
            status = "NO deberia circular en zona de restriccion normal."
        elif _vehicle_is_old_green(vehicle["year"]):
            status = "puede circular en calendario normal para ese dia."
        else:
            status = "no esta afecto en escenario normal por ser posterior a 2011."
        lines.append(
            f"- {vehicle['name']} ({vehicle['year']}, termina en {vehicle['digit']}): {status}"
        )

    lines.append(
        "\nOjo: esto cubre la restriccion normal. En episodios ambientales "
        "como alerta, preemergencia o emergencia, la autoridad puede agregar restricciones."
    )
    return "\n".join(lines)
