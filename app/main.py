from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, RedirectResponse

from app.config import settings
from app.daily_messages import build_0800_briefing, build_eye_drops_reminder
from app.linkedin import build_authorization_url, build_linkedin_ideas, exchange_authorization_code
from app.metro import build_metro_service_report, build_morning_report
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


def linkedin_redirect_uri(request: Request) -> str:
    return settings.linkedin_redirect_uri or str(request.url_for("linkedin_callback"))


@app.get("/linkedin/login")
def linkedin_login(request: Request) -> RedirectResponse:
    try:
        return RedirectResponse(build_authorization_url(linkedin_redirect_uri(request)))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/linkedin/callback", name="linkedin_callback")
async def linkedin_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> PlainTextResponse:
    if error:
        return PlainTextResponse(f"LinkedIn no autorizo la conexion: {error} {error_description or ''}", status_code=400)
    if not code:
        return PlainTextResponse("Falta el parametro code de LinkedIn.", status_code=400)

    try:
        result = await exchange_authorization_code(code, state, linkedin_redirect_uri(request))
    except Exception as exc:
        return PlainTextResponse(f"No pude conectar LinkedIn: {exc}", status_code=400)

    return PlainTextResponse(
        "LinkedIn conectado.\n\n"
        "Ahora el bot puede publicar mientras esta instancia de Lambda siga caliente.\n"
        "Para dejarlo permanente, guarda estas variables en Lambda:\n\n"
        f"LINKEDIN_ACCESS_TOKEN={result['access_token']}\n"
        f"LINKEDIN_PERSON_URN={result['person_urn']}\n"
        f"Expira en segundos: {result['expires_in']}\n\n"
        "Despues escribe en WhatsApp: post datos municipales y luego publicar."
    )


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


@app.post("/tasks/0800-briefing")
async def send_0800_briefing(request: Request) -> dict[str, str]:
    payload = await request.json() if await request.body() else {}
    verify_task_secret(payload.get("secret"))
    await send_text_message(settings.personal_whatsapp_to, await build_0800_briefing())
    return {"status": "sent", "task": "0800-briefing"}


@app.post("/tasks/eye-drops-morning")
async def send_eye_drops_morning(request: Request) -> dict[str, str]:
    payload = await request.json() if await request.body() else {}
    verify_task_secret(payload.get("secret"))
    await send_text_message(settings.personal_whatsapp_to, build_eye_drops_reminder("morning"))
    return {"status": "sent", "task": "eye-drops-morning"}


@app.post("/tasks/1830-metro")
async def send_1830_metro(request: Request) -> dict[str, str]:
    payload = await request.json() if await request.body() else {}
    verify_task_secret(payload.get("secret"))
    await send_text_message(settings.personal_whatsapp_to, await build_metro_service_report())
    return {"status": "sent", "task": "1830-metro"}


@app.post("/tasks/eye-drops-night")
async def send_eye_drops_night(request: Request) -> dict[str, str]:
    payload = await request.json() if await request.body() else {}
    verify_task_secret(payload.get("secret"))
    await send_text_message(settings.personal_whatsapp_to, build_eye_drops_reminder("night"))
    return {"status": "sent", "task": "eye-drops-night"}


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
                answer = await answer_message(text, from_number)
                try:
                    await send_text_message(from_number, answer)
                except Exception as exc:
                    print(f"Error sending WhatsApp message: {exc}")

    return {"status": "received"}
