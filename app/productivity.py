from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings


_notes_by_user: dict[str, list[str]] = {}
_agenda_by_user: dict[str, list[str]] = {}
_eye_drops_by_user: dict[str, list[str]] = {}
_reminders_by_user: dict[str, list[str]] = {}


def _now_label() -> str:
    return datetime.now(ZoneInfo(settings.timezone)).strftime("%d-%m %H:%M")


def add_note(user: str, text: str) -> str:
    if not text:
        return "Escribeme la nota despues de `nota`. Ejemplo: nota llamar a juridico por convenio."
    _notes_by_user.setdefault(user, []).append(f"{_now_label()} - {text}")
    return "Anotado en tu bitacora."


def build_daily_notes(user: str) -> str:
    notes = _notes_by_user.get(user, [])
    if not notes:
        return "Tu bitacora de hoy esta vacia. Puedes agregar algo con: nota <texto>."
    return "Bitacora de hoy:\n" + "\n".join(f"- {note}" for note in notes[-12:])


def add_agenda_item(user: str, text: str) -> str:
    if not text:
        return "Escribeme el punto despues de `agenda`. Ejemplo: agenda 15:00 reunion con Secpla."
    _agenda_by_user.setdefault(user, []).append(text)
    return "Agregado a tu agenda manual."


def build_agenda(user: str) -> str:
    items = _agenda_by_user.get(user, [])
    agenda = "Agenda manual de hoy:\n"
    if items:
        agenda += "\n".join(f"- {item}" for item in items[-10:])
    else:
        agenda += "- No tengo eventos manuales guardados."
    agenda += "\n\nPara agregar algo: agenda <hora/asunto>."
    return agenda


def record_eye_drops(user: str, text: str) -> str:
    normalized = text.lower()
    if "no" in normalized:
        status = "pendiente"
        answer = "Ok, queda pendiente. Te conviene ponertelas apenas puedas."
    else:
        status = "confirmado"
        answer = "Perfecto, dejo registradas las gotas como puestas."
    _eye_drops_by_user.setdefault(user, []).append(f"{_now_label()} - {status}")
    return answer


def build_eye_drops_status(user: str) -> str:
    records = _eye_drops_by_user.get(user, [])
    if not records:
        return "Todavia no tengo confirmaciones de gotas registradas hoy."
    return "Registro de gotas:\n" + "\n".join(f"- {record}" for record in records[-6:])


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
    if not text:
        return "Escribeme el recordatorio despues de `recordar`. Ejemplo: recordar llamar a Maria el martes a las 10."
    _reminders_by_user.setdefault(user, []).append(text)
    return (
        "Lo anote como recordatorio pendiente. "
        "Para que avise solo a una hora especifica falta conectarlo a EventBridge/DynamoDB."
    )


def build_reminders(user: str) -> str:
    reminders = _reminders_by_user.get(user, [])
    if not reminders:
        return "No tengo recordatorios manuales guardados."
    return "Recordatorios manuales:\n" + "\n".join(f"- {item}" for item in reminders[-10:])
