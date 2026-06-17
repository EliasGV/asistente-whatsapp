# Despliegue en AWS

Arquitectura recomendada:

```text
Meta WhatsApp -> API Gateway HTTP API -> Lambda Python/FastAPI
                                      -> EventBridge Scheduler
```

## Variables de entorno de Lambda

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
APP_NAME=Asistente Personal WhatsApp
```

`TASK_SECRET` debe ser un texto largo inventado por ti. Se usa para proteger tareas manuales o programadas.

## Handler de Lambda

```text
lambda_handler.handler
```

## Eventos para EventBridge Scheduler

Reporte de mañana:

```json
{
  "task": "morning-report",
  "secret": "EL_MISMO_TASK_SECRET"
}
```

Ideas LinkedIn:

```json
{
  "task": "linkedin-ideas",
  "secret": "EL_MISMO_TASK_SECRET"
}
```

## Webhook Meta

Cuando API Gateway te entregue una URL pública, usa:

```text
https://TU_API_ID.execute-api.REGION.amazonaws.com/webhook
```

Verify token:

```text
2450
```
