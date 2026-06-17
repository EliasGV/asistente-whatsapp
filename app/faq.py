import json
import re
import unicodedata
from pathlib import Path


FAQ_PATH = Path("faqs.json")


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = "".join(
        char for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"[^a-z0-9\s]", " ", text)


def load_faqs() -> list[dict[str, str]]:
    with FAQ_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_answer(message: str) -> str:
    normalized_message = normalize(message)
    faqs = load_faqs()

    for item in faqs:
        keywords = item.get("keywords", [item["question"]])
        normalized_keywords = [normalize(keyword) for keyword in keywords]
        if any(keyword and keyword in normalized_message for keyword in normalized_keywords):
            return item["answer"]

    options = "\n".join(f"- {item['question']}" for item in faqs[:10])
    return (
        "No encontré una respuesta exacta para tu consulta. "
        "Puedes preguntarme por alguno de estos temas:\n"
        f"{options}"
    )
