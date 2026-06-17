import re
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import settings


METRO_STATUS_URL = "https://www.metro.cl/el-viaje/estado-red"
LINE_NAMES = {
    "l1": "Línea 1",
    "l2": "Línea 2",
    "l3": "Línea 3",
    "l4": "Línea 4",
    "l4a": "Línea 4A",
    "l5": "Línea 5",
    "l6": "Línea 6",
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
        status = _clean_html(status_html).replace("Línea ", "Línea ").strip()
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

    try:
        lines = await fetch_metro_status()
    except Exception:
        return (
            f"Buenos días. No pude consultar metro.cl a las {now}.\n\n"
            "Revisa el estado de la red aquí: https://www.metro.cl/el-viaje/estado-red\n"
            "Para tráfico Providencia → La Cisterna, abre Google Maps o Waze antes de salir."
        )

    if not lines:
        return (
            f"Buenos días. No pude leer el detalle de líneas de Metro a las {now}.\n\n"
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
        metro_summary = "Metro aparece con sus líneas disponibles según metro.cl."

    return (
        f"Buenos días. Reporte de movilidad {now}\n\n"
        f"Metro:\n{metro_summary}\n\n"
        "Ruta Providencia → La Cisterna:\n"
        "Si vas en Metro, mira especialmente Línea 1, Línea 2 y combinaciones posibles. "
        "Si vas en auto, revisa Waze/Google Maps antes de salir porque aún no tengo una API de tráfico conectada.\n\n"
        "Fuente Metro: https://www.metro.cl/el-viaje/estado-red"
    )
