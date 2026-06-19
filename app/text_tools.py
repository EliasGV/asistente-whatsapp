import re


POST_TEMPLATES = [
    {
        "hook": "Una buena política local empieza cuando una pregunta repetida deja de verse como molestia y empieza a verse como dato.",
        "body": "Los municipios reciben señales todos los días: consultas, reclamos, solicitudes y trámites que cuesta entender. Ahí hay una fuente concreta para mejorar servicios sin esperar grandes reformas.",
        "close": "La gestión municipal también consiste en escuchar patrones y convertirlos en soluciones simples.",
    },
    {
        "hook": "Digitalizar no es solo poner un formulario en línea.",
        "body": "Digitalizar bien implica reducir fricción, explicar mejor, derivar con responsabilidad y diseñar pensando en la persona que necesita resolver algo hoy.",
        "close": "La tecnología sirve cuando hace más humano y claro el acceso al Estado local.",
    },
    {
        "hook": "El municipalismo tiene una virtud enorme: trabaja cerca de los problemas reales.",
        "body": "Esa cercanía permite detectar brechas antes que otros niveles del Estado: movilidad, acceso a información, convivencia, trámites, seguridad cotidiana y servicios básicos.",
        "close": "La pregunta es cómo transformar esa cercanía en mejores decisiones.",
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
        "Pregunta para abrir conversación: ¿qué práctica municipal concreta merece más atención?"
    )


def build_post_variant(text: str, style: str) -> str:
    text = _clean(text)
    if not text:
        return "Todavía no tengo un borrador para ajustar. Escríbeme primero: post <tema>."

    if style == "breve":
        return (
            "Borrador LinkedIn breve:\n\n"
            f"{text[:450].rstrip()}...\n\n"
            "Pregunta: ¿qué dato municipal mirarías primero?"
        )
    if style == "tecnico":
        return (
            "Borrador LinkedIn más técnico:\n\n"
            "La gestión local puede mejorar cuando convierte datos operacionales en decisiones. "
            "Consultas frecuentes, tiempos de respuesta, reclamos por territorio y fricciones de trámite "
            "permiten priorizar intervenciones, medir brechas y evaluar resultados.\n\n"
            "En municipalismo, esto puede traducirse en decisiones más oportunas: rediseñar trámites, priorizar territorios, "
            "anticipar demandas y explicar mejor los servicios disponibles.\n\n"
            "La IA aporta valor si se integra con criterios de gobernanza, trazabilidad y responsabilidad pública.\n\n"
            "Pregunta para abrir conversación: ¿qué dato operativo debería mirar primero un municipio?"
        )
    if style == "politico":
        return (
            "Borrador LinkedIn más político:\n\n"
            "El municipalismo no es solo administración cercana: es capacidad de leer la vida cotidiana y responder "
            "con soluciones concretas. Los datos y la IA pueden ayudar, pero el centro sigue siendo una decisión "
            "pública: mejorar el trato, reducir desigualdades de acceso y hacer más simple la relación con el Estado.\n\n"
            "La tecnología importa cuando fortalece esa tarea: escuchar mejor, priorizar con evidencia y actuar con sentido público.\n\n"
            "Pregunta para abrir conversación: ¿cómo hacemos que la innovación municipal se note en la vida diaria?"
        )
    if style == "datos":
        return (
            "Borrador LinkedIn con foco en datos:\n\n"
            "Un municipio produce datos todos los días: volumen de consultas, tiempos de respuesta, trámites más "
            "preguntados, sectores con más reclamos y canales con mayor demanda. El punto no es acumularlos, sino "
            "convertirlos en decisiones observables.\n\n"
            "Cuando esos datos se miran con método, pueden mostrar dónde simplificar, qué explicar mejor y qué problemas "
            "están creciendo antes de transformarse en crisis.\n\n"
            "Dato mata intuición cuando se usa con contexto y responsabilidad.\n\n"
            "Pregunta para abrir conversación: ¿qué indicador municipal sería más útil transparentar?"
        )
    return text


def build_minute(text: str) -> str:
    text = _clean(text)
    if not text:
        return (
            "Pégame el texto después de la palabra `minuta` y te lo convierto en resumen ejecutivo.\n\n"
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
