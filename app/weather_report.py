import httpx

from app.config import settings


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
LOCATIONS = [
    {"name": "Providencia", "latitude": -33.4314, "longitude": -70.6093},
    {"name": "La Cisterna", "latitude": -33.5370, "longitude": -70.6644},
]


async def _fetch_daily_temperature(location: dict[str, float | str]) -> dict[str, str | float]:
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "daily": "temperature_2m_min,temperature_2m_max",
        "forecast_days": 1,
        "timezone": settings.timezone,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(OPEN_METEO_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    daily = payload["daily"]
    return {
        "name": str(location["name"]),
        "min": round(float(daily["temperature_2m_min"][0])),
        "max": round(float(daily["temperature_2m_max"][0])),
    }


async def build_weather_report() -> str:
    try:
        results = []
        for location in LOCATIONS:
            results.append(await _fetch_daily_temperature(location))
    except Exception:
        return (
            "Clima:\n"
            "No pude consultar la temperatura en este momento. "
            "Puedes revisar una fuente meteorologica antes de salir."
        )

    lines = ["Clima de hoy:"]
    for item in results:
        lines.append(f"- {item['name']}: minima {item['min']} C, maxima {item['max']} C.")
    lines.append("Fuente: Open-Meteo.")
    return "\n".join(lines)
