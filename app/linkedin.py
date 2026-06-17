from datetime import date

from app.text_tools import build_custom_post


TOPICS = [
    {
        "title": "Datos municipales para decidir mejor",
        "angle": "Como las preguntas, reclamos y tramites repetidos pueden orientar prioridades reales de gestion local.",
    },
    {
        "title": "IA aplicada al municipalismo",
        "angle": "Usar IA para ordenar informacion, anticipar necesidades y mejorar la experiencia ciudadana sin perder criterio publico.",
    },
    {
        "title": "Municipalismo de cercania con evidencia",
        "angle": "La cercania municipal se vuelve mas potente cuando se combina con datos simples, oportunos y accionables.",
    },
    {
        "title": "Digitalizacion con trato humano",
        "angle": "Automatizar lo repetitivo para liberar tiempo, explicar mejor y derivar con responsabilidad.",
    },
    {
        "title": "Transparencia util",
        "angle": "Pasar de publicar informacion a hacerla encontrable, comprensible y usable por vecinos y equipos municipales.",
    },
]


def build_linkedin_ideas() -> str:
    start = date(2026, 1, 1).toordinal()
    topic = TOPICS[(date.today().toordinal() - start) % len(TOPICS)]

    draft = (
        f"Propuesta LinkedIn: {topic['title']}\n\n"
        f"Idea central: {topic['angle']}\n\n"
        "Borrador:\n"
        "El municipalismo tiene una ventaja enorme: esta cerca de los problemas cotidianos. "
        "Esa cercania genera datos todos los dias: consultas, tiempos de respuesta, reclamos, "
        "tramites dificiles de entender y preguntas que se repiten.\n\n"
        "La IA puede ayudar a ordenar esas senales, pero el valor publico no esta solo en automatizar. "
        "Esta en convertir informacion dispersa en mejores decisiones, mejor comunicacion y servicios mas simples.\n\n"
        "Cuando un municipio escucha patrones y actua sobre ellos, la tecnologia deja de ser decoracion "
        "y se transforma en capacidad institucional.\n\n"
        "Pregunta para abrir conversacion: que dato municipal deberiamos mirar con mas atencion?"
    )

    return (
        "Mediodia: te dejo una propuesta de publicacion sobre datos, IA y municipalismo.\n\n"
        f"{draft}\n\n"
        "Si te gusta, respondeme: aprobar. Si quieres otra linea, respondeme: otra idea."
    )


def build_linkedin_post(topic: str = "") -> str:
    return build_custom_post(topic)
