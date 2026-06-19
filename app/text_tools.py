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


def build_post_variant(text: str, style: str) -> str:
    text = _clean(text)
    if not text:
        return "Todavia no tengo un borrador para ajustar. Escribeme primero: post <tema>."

    if style == "breve":
        return (
            "Borrador LinkedIn breve:\n\n"
            f"{text[:450].rstrip()}...\n\n"
            "Pregunta: que dato municipal mirarias primero?"
        )
    if style == "tecnico":
        return (
            "Borrador LinkedIn mas tecnico:\n\n"
            "La gestion local puede mejorar cuando convierte datos operacionales en decisiones. "
            "Consultas frecuentes, tiempos de respuesta, reclamos por territorio y fricciones de tramite "
            "permiten priorizar intervenciones, medir brechas y evaluar resultados.\n\n"
            f"Base del texto: {text}\n\n"
            "La IA aporta valor si se integra con criterios de gobernanza, trazabilidad y responsabilidad publica."
        )
    if style == "politico":
        return (
            "Borrador LinkedIn mas politico:\n\n"
            "El municipalismo no es solo administracion cercana: es capacidad de leer la vida cotidiana y responder "
            "con soluciones concretas. Los datos y la IA pueden ayudar, pero el centro sigue siendo una decision "
            "publica: mejorar el trato, reducir desigualdades de acceso y hacer mas simple la relacion con el Estado.\n\n"
            f"Base del texto: {text}"
        )
    if style == "datos":
        return (
            "Borrador LinkedIn con foco en datos:\n\n"
            "Un municipio produce datos todos los dias: volumen de consultas, tiempos de respuesta, tramites mas "
            "preguntados, sectores con mas reclamos y canales con mayor demanda. El punto no es acumularlos, sino "
            "convertirlos en decisiones observables.\n\n"
            f"Base del texto: {text}\n\n"
            "Dato mata intuicion cuando se usa con contexto y responsabilidad."
        )
    return text


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
