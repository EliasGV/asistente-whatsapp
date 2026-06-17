from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.linkedin import build_linkedin_ideas
from app.metro import build_morning_report
from app.personal_bot import answer_message
from app.scheduler import start_scheduler
from app.whatsapp import send_text_message


app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def startup() -> None:
    await start_scheduler()


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


def verify_task_secret(secret: str | None) -> None:
    if settings.task_secret and secret != settings.task_secret:
        raise HTTPException(status_code=403, detail="Invalid task secret")


@app.post("/tasks/morning-report")
async def send_morning_report(request: Request) -> dict[str, str]:
    payload = await request.json() if await request.body() else {}
    verify_task_secret(payload.get("secret"))
    await send_text_message(settings.personal_whatsapp_to, await build_morning_report())
    return {"status": "sent", "task": "morning-report"}


@app.post("/tasks/linkedin-ideas")
async def send_linkedin_ideas(request: Request) -> dict[str, str]:
    payload = await request.json() if await request.body() else {}
    verify_task_secret(payload.get("secret"))
    await send_text_message(settings.personal_whatsapp_to, build_linkedin_ideas())
    return {"status": "sent", "task": "linkedin-ideas"}


@app.get("/webhook")
def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> PlainTextResponse:
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return PlainTextResponse(hub_challenge or "")
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook")
async def receive_message(request: Request) -> dict[str, str]:
    payload = await request.json()

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue

                from_number = message["from"]
                text = message["text"]["body"]
                answer = await answer_message(text)
                try:
                    await send_text_message(from_number, answer)
                except Exception as exc:
                    print(f"Error sending WhatsApp message: {exc}")

    return {"status": "received"}
