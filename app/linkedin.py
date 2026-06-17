from datetime import date

from app.text_tools import build_custom_post


TOPICS = [
    {
        "title": "Municipalismo de cercania",
        "angle": "Los municipios como primera puerta del Estado para resolver problemas cotidianos.",
    },
    {
        "title": "Datos para mejorar servicios locales",
        "angle": "Usar preguntas frecuentes, reclamos y atencion ciudadana para priorizar informacion y tramites.",
    },
    {
        "title": "Digitalizacion con trato humano",
        "angle": "Automatizar lo repetitivo sin perder orientacion clara ni derivacion responsable.",
    },
    {
        "title": "Transparencia util",
        "angle": "Pasar de publicar informacion a hacerla encontrable, accionable y comprensible.",
    },
    {
        "title": "Municipios y movilidad cotidiana",
        "angle": "Como las decisiones locales impactan trayectos, seguridad vial y acceso a servicios.",
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
        "ordenar informacion y transformar consultas repetidas en mejores servicios.\n\n"
        "Cuando una comunidad pregunta muchas veces por lo mismo, no solo esta pidiendo una respuesta: "
        "esta mostrando una brecha de comunicacion, acceso o diseno del tramite.\n\n"
        "Ahi hay una oportunidad enorme para los gobiernos locales: usar datos simples de atencion ciudadana "
        "para anticiparse, explicar mejor y llegar antes.\n\n"
        "Pregunta para abrir conversacion: que servicio municipal deberia ser mucho mas facil de encontrar y usar?"
    )

    return (
        "Mediodia: te dejo una propuesta de publicacion sobre municipalismo.\n\n"
        f"{draft}\n\n"
        "Si te gusta, respondeme: aprobar. Si quieres otra linea, respondeme: otra idea."
    )


def build_linkedin_post(topic: str = "") -> str:
    return build_custom_post(topic)
