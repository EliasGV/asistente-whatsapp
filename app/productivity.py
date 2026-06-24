from app.memory_store import delete_matching_items, list_items, mark_done, now_label, put_item, search_items


def add_note(user: str, text: str) -> str:
    if not text:
        return "Escribeme la nota despues de `nota`. Ejemplo: nota llamar a juridico por convenio."
    put_item(user, "note", text, {"label": now_label()})
    return "Anotado en tu bitacora."


def build_daily_notes(user: str) -> str:
    notes = list_items(user, "note", limit=12)
    if not notes:
        return "Tu bitacora esta vacia. Puedes agregar algo con: nota <texto>."
    return "Bitacora reciente:\n" + "\n".join(f"- {item.get('label', item['created_at'])} - {item['text']}" for item in notes)


def add_agenda_item(user: str, text: str) -> str:
    if not text:
        return "Escribeme el punto despues de `agenda`. Ejemplo: agenda 15:00 reunion con Secpla."
    put_item(user, "agenda", text, {"label": now_label()})
    return "Agregado a tu agenda manual."


def build_agenda(user: str) -> str:
    items = list_items(user, "agenda", limit=10)
    agenda = "Agenda manual:\n"
    if items:
        agenda += "\n".join(f"- {item['text']}" for item in items)
    else:
        agenda += "- No tengo eventos manuales guardados."
    agenda += "\n\nPara agregar algo: agenda <hora/asunto>."
    return agenda


def record_eye_drops(user: str, text: str) -> str:
    normalized = text.lower()
    if "no" in normalized or "pendiente" in normalized:
        status = "pendiente"
        answer = "Ok, queda pendiente. Te conviene ponertelas apenas puedas."
    else:
        status = "confirmado"
        answer = "Perfecto, dejo registradas las gotas como puestas."
    put_item(user, "eye_drops", status, {"label": now_label(), "status": status})
    return answer


def build_eye_drops_status(user: str) -> str:
    records = list_items(user, "eye_drops", limit=6)
    if not records:
        return (
            "Todavia no tengo confirmaciones de gotas registradas.\n\n"
            "Cuando te pregunte por las gotas puedes responder: si, listo, me las puse, no o pendiente."
        )

    latest = records[-1]
    latest_status = latest.get("status", latest.get("text", "registrado"))
    lines = [
        "Registro de gotas:",
        f"Ultimo estado: {latest_status} ({latest.get('label', latest['created_at'])})",
        "",
        "Ultimos registros:",
    ]
    lines.extend(
        f"- {item.get('label', item['created_at'])} - {item.get('status', item.get('text', 'registrado'))}"
        for item in records
    )
    return "\n".join(lines)


def build_work_checklist() -> str:
    return (
        "Checklist laboral:\n"
        "- Revisar agenda del dia.\n"
        "- Revisar correos urgentes.\n"
        "- Definir 1 prioridad principal.\n"
        "- Revisar compromisos pendientes.\n"
        "- Preparar minuta o seguimiento de reuniones clave.\n"
        "- Revisar si hay algo publicable sobre datos, IA o municipalismo."
    )


def add_reminder(user: str, text: str) -> str:
    from app.reminders import create_real_reminder

    return create_real_reminder(user, text)


def build_reminders(user: str) -> str:
    reminders = list_items(user, "reminder", limit=10)
    if not reminders:
        return "No tengo recordatorios guardados."
    return "Recordatorios:\n" + "\n".join(
        f"- {item['text']} ({item.get('status', 'scheduled')}, {item.get('run_at', 'sin fecha')})"
        for item in reminders
    )


def mark_commitment_done(user: str, text: str) -> str:
    if mark_done(user, "reminder", text) or mark_done(user, "commitment", text):
        return "Listo, lo marque como cumplido."
    return "No encontre un pendiente parecido. Prueba con una palabra clave del recordatorio."


def search_memory(user: str, text: str) -> str:
    if not text:
        return "Escribeme que quieres buscar. Ejemplo: buscar memoria juridico."
    matches = search_items(user, text)
    if not matches:
        return f"No encontre recuerdos, notas o pendientes sobre: {text}."
    lines = [f"Memoria encontrada sobre '{text}':"]
    for item in matches:
        lines.append(f"- {item.get('category', 'item')}: {item.get('text', '')}")
    return "\n".join(lines)


def delete_memory(user: str, text: str) -> str:
    normalized = text.lower().strip()
    if normalized in {"terapia", "memoria terapia"}:
        count = delete_matching_items(user, "therapy")
        return f"Borre {count} recuerdo(s) de terapia."
    if normalized in {"todo", "toda", "todo todo"}:
        count = delete_matching_items(user, None)
        return f"Borre {count} elemento(s) de memoria."
    if normalized:
        count = delete_matching_items(user, None, normalized)
        return f"Borre {count} elemento(s) que coincidian con: {text}."
    return "Dime que memoria borrar. Ejemplo: borrar memoria terapia, borrar memoria juridico, borrar memoria todo."


def add_therapy_memory(user: str, text: str) -> str:
    if not text:
        return (
            "Escribeme el recuerdo despues de `recuerdo`.\n\n"
            "Ejemplo: recuerdo hoy me senti sobrepasado despues de una reunion y quiero hablarlo en terapia."
        )
    put_item(user, "therapy", text, {"label": now_label()})
    return "Lo guarde para tu resumen previo a terapia."


def build_therapy_summary(user: str) -> str:
    memories = list_items(user, "therapy", limit=12)
    if not memories:
        return (
            "Todavia no tengo recuerdos guardados para terapia.\n\n"
            "Puedes agregar uno con: recuerdo <texto>."
        )

    text = " ".join(item["text"] for item in memories).lower()
    themes = []
    theme_keywords = {
        "estres o sobrecarga": ["estres", "sobrecarg", "cansad", "agotad", "ansiedad", "ansioso"],
        "trabajo y responsabilidades": ["trabajo", "reunion", "correo", "municip", "jef", "responsabilidad"],
        "vinculos o conversaciones dificiles": ["familia", "pareja", "amigo", "convers", "discusion"],
        "salud y autocuidado": ["salud", "gotas", "glaucoma", "dorm", "cuerpo", "medico"],
        "decisiones o incertidumbre": ["decidir", "decision", "duda", "incertidumbre", "miedo"],
    }
    for theme, keywords in theme_keywords.items():
        if any(keyword in text for keyword in keywords):
            themes.append(theme)
    if not themes:
        themes.append("experiencias relevantes de la semana")

    lines = ["Resumen previo a terapia:", "", "Temas que aparecen:"]
    lines.extend(f"- {theme}" for theme in themes[:5])
    lines.append("\nRecuerdos recientes:")
    lines.extend(f"- {item.get('label', item['created_at'])} - {item['text']}" for item in memories)
    lines.append(
        "\nPreguntas posibles para llevar:\n"
        "- Que se repitio emocionalmente en estos dias?\n"
        "- Que situacion me dejo mas activado o incomodo?\n"
        "- Que necesito pedir, soltar o ordenar?\n"
        "- Que senal de autocuidado deberia tomar mas en serio?"
    )
    lines.append("\nNota: esto ayuda a preparar la conversacion con tu terapeuta, no es una interpretacion clinica.")
    return "\n".join(lines)
