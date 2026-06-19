import hashlib
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import settings
from app.productivity import add_therapy_memory
from app.whatsapp import GRAPH_API_VERSION


_processed_jobs: set[str] = set()


def _safe_user_key(user: str) -> str:
    return hashlib.sha256(user.encode("utf-8")).hexdigest()[:16]


def _job_name(user: str, message_id: str) -> str:
    raw = f"wa-{_safe_user_key(user)}-{message_id[-24:]}"
    return re.sub(r"[^0-9A-Za-z._-]", "-", raw)[:200]


def _media_format(mime_type: str) -> str:
    mime_type = (mime_type or "").lower()
    if "ogg" in mime_type:
        return "ogg"
    if "mpeg" in mime_type or "mp3" in mime_type:
        return "mp3"
    if "mp4" in mime_type or "m4a" in mime_type:
        return "mp4"
    if "wav" in mime_type:
        return "wav"
    if "webm" in mime_type:
        return "webm"
    return "ogg"


async def _download_whatsapp_media(media_id: str) -> tuple[bytes, str]:
    if not media_id:
        raise RuntimeError("Missing WhatsApp media id.")
    if not settings.whatsapp_token:
        raise RuntimeError("Missing WHATSAPP_TOKEN.")

    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        metadata_response = await client.get(f"https://graph.facebook.com/{GRAPH_API_VERSION}/{media_id}")
        metadata_response.raise_for_status()
        metadata = metadata_response.json()

        media_response = await client.get(metadata["url"])
        media_response.raise_for_status()
        return media_response.content, metadata.get("mime_type", "audio/ogg")


async def start_whatsapp_audio_transcription(user: str, media_id: str, message_id: str) -> str:
    if not settings.transcribe_bucket:
        raise RuntimeError("Missing TRANSCRIBE_BUCKET.")

    boto3 = __import__("boto3")
    audio_bytes, mime_type = await _download_whatsapp_media(media_id)
    job_name = _job_name(user, message_id)
    media_format = _media_format(mime_type)
    user_key = _safe_user_key(user)
    timestamp = datetime.now(ZoneInfo(settings.timezone)).strftime("%Y%m%d-%H%M%S")
    extension = "ogg" if media_format == "ogg" else media_format
    audio_key = f"{settings.transcribe_audio_prefix}{user_key}/{timestamp}-{job_name}.{extension}"

    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=settings.transcribe_bucket,
        Key=audio_key,
        Body=audio_bytes,
        ContentType=mime_type,
    )

    transcribe = boto3.client("transcribe")
    try:
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            LanguageCode=settings.transcribe_language_code,
            MediaFormat=media_format,
            Media={"MediaFileUri": f"s3://{settings.transcribe_bucket}/{audio_key}"},
            OutputBucketName=settings.transcribe_bucket,
            OutputKey=f"{settings.transcribe_output_prefix}{user_key}/{job_name}.json",
        )
    except transcribe.exceptions.ConflictException:
        pass

    return job_name


async def collect_finished_audio_memories(user: str) -> str:
    if not settings.transcribe_bucket:
        return "Falta configurar TRANSCRIBE_BUCKET para usar transcripción de audios."

    boto3 = __import__("boto3")
    transcribe = boto3.client("transcribe")
    prefix = f"wa-{_safe_user_key(user)}-"
    response = transcribe.list_transcription_jobs(
        Status="COMPLETED",
        JobNameContains=prefix,
        MaxResults=10,
    )

    jobs = response.get("TranscriptionJobSummaries", [])
    if not jobs:
        return "Todavía no encontré audios transcritos. Si acabas de mandar uno, prueba de nuevo en unos minutos con: audios."

    s3 = boto3.client("s3")
    added = []
    for job in jobs:
        job_name = job["TranscriptionJobName"]
        if job_name in _processed_jobs:
            continue
        key = f"{settings.transcribe_output_prefix}{_safe_user_key(user)}/{job_name}.json"
        try:
            obj = s3.get_object(Bucket=settings.transcribe_bucket, Key=key)
            payload = json.loads(obj["Body"].read().decode("utf-8"))
            transcript = payload["results"]["transcripts"][0]["transcript"].strip()
        except Exception:
            continue
        if not transcript:
            continue
        add_therapy_memory(user, f"Audio transcrito: {transcript}")
        _processed_jobs.add(job_name)
        added.append(transcript)

    if not added:
        return "Encontré trabajos completados, pero no pude agregar una transcripción nueva. Puede que ya estuvieran revisados."

    preview = "\n\n".join(f"- {item[:700]}" for item in added[:3])
    return (
        "Agregué estos audios a tu memoria para terapia:\n\n"
        f"{preview}\n\n"
        "Cuando quieras preparar la sesión, escríbeme: terapia."
    )
