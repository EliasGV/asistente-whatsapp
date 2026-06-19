import re
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import settings
from app.vehicle_restriction import build_vehicle_restriction_report


METRO_STATUS_URL = "https://www.metro.cl/el-viaje/estado-red"
LINE_NAMES = {
    "l1": "Linea 1",
    "l2": "Linea 2",
    "l3": "Linea 3",
    "l4": "Linea 4",
    "l4a": "Linea 4A",
    "l5": "Linea 5",
    "l6": "Linea 6",
}


def _clean_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_line_cards(html: str) -> list[dict[str, str]]:
    cards = re.findall(
        r'<div class="col-2"><img src="/images/ico-(l\d+a?)\.svg".*?</div>\s*'
        r'<div class="col-8"><p.*?>(.*?)</p></div>\s*'
        r'<div class="col-2"><img src="/images/(ico-estado-[^"]+)\.svg".*?</div>.*?'
        r'<p class="margin-bottom-0">(.*?)</p>.*?'
        r'<div class="col-md-8 col-12">(.*?)</div>\s*</div>',
        html,
        flags=re.S | re.I,
    )

    lines = []
    for code, status_html, icon, route_html, details_html in cards:
        status = _clean_html(status_html).replace("Linea ", "Linea ").strip()
        route = _clean_html(route_html)
        details = _clean_html(details_html)
        lines.append(
            {
                "line": LINE_NAMES.get(code.lower(), code.upper()),
                "status": status,
                "icon": icon,
                "route": route,
                "details": details,
            }
        )
    return lines


async def fetch_metro_status() -> list[dict[str, str]]:
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers) as client:
        response = await client.get(METRO_STATUS_URL)
        response.raise_for_status()
    return _parse_line_cards(response.text)


async def build_morning_report() -> str:
    now = datetime.now(ZoneInfo(settings.timezone)).strftime("%H:%M")
    vehicle_report = build_vehicle_restriction_report()

    try:
        lines = await fetch_metro_status()
    except Exception:
        return (
            f"Buenos dias. No pude consultar metro.cl a las {now}.\n\n"
            "Revisa el estado de la red aqui: https://www.metro.cl/el-viaje/estado-red\n\n"
            f"{vehicle_report}\n\n"
            "Para trafico Providencia -> La Cisterna, abre Google Maps o Waze antes de salir."
        )

    if not lines:
        return (
            f"Buenos dias. No pude leer el detalle de lineas de Metro a las {now}.\n\n"
            f"{vehicle_report}\n\n"
            "Fuente: https://www.metro.cl/el-viaje/estado-red"
        )

    problem_lines = [
        item for item in lines
        if "disponible" not in item["status"].lower() or item["details"]
    ]

    if problem_lines:
        metro_summary = "\n".join(
            f"- {item['line']}: {item['status']}. {item['details']}".strip()
            for item in problem_lines
        )
    else:
        metro_summary = "Metro aparece con sus lineas disponibles segun metro.cl."

    return (
        f"Buenos dias. Reporte de movilidad {now}\n\n"
        f"Metro:\n{metro_summary}\n\n"
        f"{vehicle_report}\n\n"
        "Ruta Providencia -> La Cisterna:\n"
        "Si vas en Metro, mira especialmente Linea 1, Linea 2 y combinaciones posibles. "
        "Si vas en auto, revisa Waze/Google Maps antes de salir porque aun no tengo una API de trafico conectada.\n\n"
        "Fuente Metro: https://www.metro.cl/el-viaje/estado-red"
    )


async def build_metro_service_report() -> str:
    now = datetime.now(ZoneInfo(settings.timezone)).strftime("%H:%M")
    try:
        lines = await fetch_metro_status()
    except Exception:
        return (
            f"Estado Metro {now}:\n"
            "No pude consultar metro.cl en este momento.\n\n"
            "Fuente: https://www.metro.cl/el-viaje/estado-red"
        )

    if not lines:
        return (
            f"Estado Metro {now}:\n"
            "No pude leer el detalle de lineas desde metro.cl.\n\n"
            "Fuente: https://www.metro.cl/el-viaje/estado-red"
        )

    problem_lines = [
        item for item in lines
        if "disponible" not in item["status"].lower() or item["details"]
    ]

    if problem_lines:
        metro_summary = "\n".join(
            f"- {item['line']}: {item['status']}. {item['details']}".strip()
            for item in problem_lines
        )
    else:
        metro_summary = "Metro aparece con sus lineas disponibles segun metro.cl."

    return (
        f"Estado Metro {now}:\n"
        f"{metro_summary}\n\n"
        "Fuente: https://www.metro.cl/el-viaje/estado-red"
    )
