import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import httpx


NEWS_QUERY = "municipalismo municipios Chile gestion municipal gobiernos locales"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=es-419&gl=CL&ceid=CL:es-419"


def _clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


async def fetch_municipal_news(limit: int = 5) -> list[dict[str, str]]:
    url = GOOGLE_NEWS_RSS.format(query=quote_plus(NEWS_QUERY))
    headers = {"User-Agent": "Mozilla/5.0"}

    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()

    root = ET.fromstring(response.text)
    items = []
    for item in root.findall(".//item")[:limit]:
        title = _clean_text(item.findtext("title"))
        link = _clean_text(item.findtext("link"))
        source = item.find("{http://www.w3.org/2005/Atom}source")
        source_name = _clean_text(source.text if source is not None else "")
        items.append({"title": title, "link": link, "source": source_name})
    return items


async def build_news_digest() -> str:
    try:
        items = await fetch_municipal_news()
    except Exception:
        return (
            "No pude consultar noticias ahora. Intenta de nuevo con `noticias` en unos minutos.\n\n"
            "Fuente configurada: Google News RSS sobre municipalismo, municipios y gestion local en Chile."
        )

    if not items:
        return "No encontre noticias recientes sobre municipalismo en la fuente configurada."

    lines = ["Noticias para mirar con ojo municipal:"]
    for index, item in enumerate(items, start=1):
        source = f" ({item['source']})" if item["source"] else ""
        lines.append(f"{index}. {item['title']}{source}\n{item['link']}")

    lines.append(
        "\nLectura sugerida: revisa si alguna noticia abre una idea sobre gestion local, "
        "servicios municipales, datos publicos o confianza ciudadana."
    )
    return "\n\n".join(lines)
