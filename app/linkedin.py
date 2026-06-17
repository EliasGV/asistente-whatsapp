from datetime import date


TOPICS = [
    {
        "title": "Municipalismo de cercanía",
        "angle": "Los municipios como primera puerta del Estado para resolver problemas cotidianos.",
    },
    {
        "title": "Datos para mejorar servicios locales",
        "angle": "Usar preguntas frecuentes, reclamos y atención ciudadana para priorizar información y trámites.",
    },
    {
        "title": "Digitalización con trato humano",
        "angle": "Automatizar lo repetitivo sin perder orientación clara ni derivación responsable.",
    },
    {
        "title": "Transparencia útil",
        "angle": "Pasar de publicar información a hacerla encontrable, accionable y comprensible.",
    },
    {
        "title": "Municipios y movilidad cotidiana",
        "angle": "Cómo las decisiones locales impactan trayectos, seguridad vial y acceso a servicios.",
    },
]


def build_linkedin_ideas() -> str:
    start = date(2026, 1, 1).toordinal()
    topic = TOPICS[(date.today().toordinal() - start) % len(TOPICS)]

    draft = (
        f"Propuesta LinkedIn: {topic['title']}\n\n"
        f"Idea central: {topic['angle']}\n\n"
        "Borrador:\n"
        "El municipalismo se juega en lo concreto: en la capacidad de escuchar patrones, "
        "ordenar información y transformar consultas repetidas en mejores servicios.\n\n"
        "Cuando una comunidad pregunta muchas veces por lo mismo, no solo está pidiendo una respuesta: "
        "está mostrando una brecha de comunicación, acceso o diseño del trámite.\n\n"
        "Ahí hay una oportunidad enorme para los gobiernos locales: usar datos simples de atención ciudadana "
        "para anticiparse, explicar mejor y llegar antes.\n\n"
        "Pregunta para abrir conversación: ¿qué servicio municipal debería ser mucho más fácil de encontrar y usar?"
    )

    return (
        "Mediodía: te dejo una propuesta de publicación sobre municipalismo.\n\n"
        f"{draft}\n\n"
        "Si te gusta, respóndeme: aprobar. Si quieres otra línea, respóndeme: otra idea."
    )
