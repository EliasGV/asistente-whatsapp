import re


POST_TEMPLATES = [
    {
        "hook": "Una buena politica local empieza cuando una pregunta repetida deja de verse como molestia y empieza a verse como dato.",
        "body": "Los municipios reciben senales todos los dias: consultas, reclamos, solicitudes y tramites que cuestan entender. Ahi hay una fuente concreta para mejorar servicios sin esperar grandes reformas.",
        "close": "La gestion municipal tambien consiste en escuchar patrones y convertirlos en soluciones simples.",
    },
    {
        "hook": "Digitalizar no es solo poner un formulario en linea.",
        "body": "Digitalizar bien implica reducir friccion, explicar mejor, derivar con responsabilidad y disenar pensando en la persona que necesita resolver algo hoy.",
        "close": "La tecnologia sirve cuando hace mas humano y claro el acceso al Estado local.",
    },
    {
        "hook": "El municipalismo tiene una virtud enorme: trabaja cerca de los problemas reales.",
        "body": "Esa cercania permite detectar brechas antes que otros niveles del Estado: movilidad, acceso a informacion, convivencia, tramites, seguridad cotidiana y servicios basicos.",
        "close": "La pregunta es como transformar esa cercania en mejores decisiones.",
    },
]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+", _clean(text))
    return [piece.strip() for piece in pieces if len(piece.strip()) > 20]


def build_custom_post(topic: str = "") -> str:
    topic = _clean(topic)
    template = POST_TEMPLATES[len(topic) % len(POST_TEMPLATES)]
    topic_line = f"\n\nTema pedido: {topic}" if topic else ""

    return (
        "Borrador LinkedIn:\n\n"
        f"{template['hook']}{topic_line}\n\n"
        f"{template['body']}\n\n"
        f"{template['close']}\n\n"
        "Pregunta para abrir conversacion: que practica municipal concreta merece mas atencion?"
    )


def build_minute(text: str) -> str:
    text = _clean(text)
    if not text:
        return (
            "Pegame el texto despues de la palabra `minuta` y te lo convierto en resumen ejecutivo.\n\n"
            "Ejemplo: minuta hoy revisamos tres temas..."
        )

    sentences = _sentences(text)
    if not sentences:
        sentences = [text]

    key_points = sentences[:5]
    actions = [
        sentence for sentence in sentences
        if any(word in sentence.lower() for word in ["debe", "hay que", "queda", "acord", "revisar", "enviar", "coordinar"])
    ][:3]

    result = ["Minuta ejecutiva:"]
    result.append("\nResumen:\n" + " ".join(key_points[:3]))
    result.append("\nPuntos clave:")
    result.extend(f"- {point}" for point in key_points)

    if actions:
        result.append("\nPosibles acciones:")
        result.extend(f"- {action}" for action in actions)

    result.append("\nSiguiente paso sugerido: validar responsables, plazos y acuerdos pendientes.")
    return "\n".join(result)
