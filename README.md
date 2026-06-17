# Asistente Personal por WhatsApp

Bot personal conectado a WhatsApp Cloud API.

## Comandos

- `metro`: reporte de movilidad con estado de lineas desde `https://www.metro.cl/el-viaje/estado-red`.
- `noticias`: titulares recientes sobre municipalismo, municipios y gestion local.
- `linkedin`: propuesta diaria de publicacion sobre municipalismo.
- `post <tema>`: borrador LinkedIn sobre el tema que indiques.
- `minuta <texto>`: convierte texto largo en minuta ejecutiva.
- `aprobar`: confirma que una idea queda aprobada para que la publiques manualmente.
- `ayuda`: muestra comandos disponibles.

## Configuracion

Copia `.env.example` como `.env` y completa:

```text
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
PERSONAL_WHATSAPP_TO=56957245045
ENABLE_SCHEDULER=false
MORNING_REPORT_TIME=08:00
LINKEDIN_IDEAS_TIME=12:00
TIMEZONE=America/Santiago
TASK_SECRET=
APP_NAME=Asistente Personal WhatsApp
```

## Ejecutar Local

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

## AWS Lambda

Handler:

```text
lambda_handler.handler
```

Webhook Meta:

```text
https://TU_FUNCTION_URL/webhook
```

Verify token:

```text
2450
```

Suscribir el campo:

```text
messages
```

## Programacion Diaria

El codigo incluye scheduler para enviar mensajes a:

- `MORNING_REPORT_TIME`, por defecto `08:00`
- `LINKEDIN_IDEAS_TIME`, por defecto `12:00`

Para activarlo:

```text
ENABLE_SCHEDULER=true
```

Importante: WhatsApp Cloud API puede exigir plantillas aprobadas por Meta para mensajes iniciados por el bot fuera de la ventana de conversacion. Si el envio programado falla por politica de WhatsApp, hay que crear templates aprobados o mantener la interaccion dentro de la ventana permitida.
