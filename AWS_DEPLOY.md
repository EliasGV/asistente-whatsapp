# Despliegue en AWS

Arquitectura recomendada:

```text
Meta WhatsApp -> Lambda Function URL -> Lambda Python/FastAPI
                                      -> EventBridge Scheduler
```

## Variables De Entorno De Lambda

Configura estas variables en AWS Lambda:

```text
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=2450
PERSONAL_WHATSAPP_TO=56957245045
ENABLE_SCHEDULER=false
MORNING_REPORT_TIME=08:00
LINKEDIN_IDEAS_TIME=12:00
TIMEZONE=America/Santiago
TASK_SECRET=
VEHICLE_ONE_YEAR=2010
VEHICLE_ONE_DIGIT=2
VEHICLE_TWO_YEAR=2019
VEHICLE_TWO_DIGIT=8
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_REDIRECT_URI=https://i4p7wvgqyivpri7ysmcjcwweoe0uoekj.lambda-url.us-east-1.on.aws/linkedin/callback
LINKEDIN_STATE_SECRET=
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_PERSON_URN=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://i4p7wvgqyivpri7ysmcjcwweoe0uoekj.lambda-url.us-east-1.on.aws/gmail/callback
GOOGLE_STATE_SECRET=
GMAIL_ACCESS_TOKEN=
GMAIL_REFRESH_TOKEN=
TRANSCRIBE_BUCKET=
TRANSCRIBE_LANGUAGE_CODE=es-US
TRANSCRIBE_OUTPUT_PREFIX=transcripts/
TRANSCRIBE_AUDIO_PREFIX=audio/
MEMORY_TABLE_NAME=
REMINDER_SCHEDULER_ROLE_ARN=
REMINDER_LAMBDA_ARN=
APP_NAME=Asistente Personal WhatsApp
```

`TASK_SECRET` debe ser un texto largo inventado por ti. Se usa para proteger tareas manuales o programadas.

## Handler De Lambda

```text
lambda_handler.handler
```

## Eventos Para EventBridge Scheduler

Reporte 08:00:

```json
{
  "task": "0800-briefing",
  "secret": "EL_MISMO_TASK_SECRET"
}
```

Gotas 09:00:

```json
{
  "task": "eye-drops-morning",
  "secret": "EL_MISMO_TASK_SECRET"
}
```

Seguimiento gotas 09:30, solo avisa si no confirmaste:

```json
{
  "task": "eye-drops-morning-followup",
  "secret": "EL_MISMO_TASK_SECRET"
}
```

Metro 18:30:

```json
{
  "task": "1830-metro",
  "secret": "EL_MISMO_TASK_SECRET"
}
```

Gotas 21:00:

```json
{
  "task": "eye-drops-night",
  "secret": "EL_MISMO_TASK_SECRET"
}
```

Cierre diario 21:30:

```json
{
  "task": "nightly-summary",
  "secret": "EL_MISMO_TASK_SECRET"
}
```

Seguimiento gotas noche 21:45, solo avisa si no confirmaste:

```json
{
  "task": "eye-drops-night-followup",
  "secret": "EL_MISMO_TASK_SECRET"
}
```

## Webhook Meta

Webhook:

```text
https://TU_FUNCTION_URL/webhook
```

Verify token:

```text
2450
```
