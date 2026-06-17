# Asistente Personal por WhatsApp

Bot personal conectado a WhatsApp Cloud API.

## Qué hace

- Si escribes `metro`, responde con un reporte de movilidad:
  - estado de líneas desde `https://www.metro.cl/el-viaje/estado-red`
  - nota para ruta Providencia -> La Cisterna
- Si escribes `linkedin`, propone una publicación sobre municipalismo.
- Si escribes `aprobar`, confirma que la idea queda aprobada para que la publiques manualmente.
- Si escribes `ayuda`, muestra comandos disponibles.

## Configuración

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
APP_NAME=Asistente Personal WhatsApp
```

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

## Webhook de Meta

URL local publicada por túnel:

```text
https://tu-url-publica/webhook
```

Verify token:

```text
2450
```

Suscribir el campo:

```text
messages
```

## Programación diaria

El código incluye scheduler para enviar mensajes a:

- `MORNING_REPORT_TIME`, por defecto `08:00`
- `LINKEDIN_IDEAS_TIME`, por defecto `12:00`

Para activarlo:

```text
ENABLE_SCHEDULER=true
```

Importante: WhatsApp Cloud API puede exigir plantillas aprobadas por Meta para mensajes iniciados por el bot fuera de la ventana de conversación. Si el envío programado falla por política de WhatsApp, hay que crear templates aprobados o mantener la interacción dentro de la ventana permitida.

## Tráfico

El bot todavía no tiene una API de tráfico conectada. Por ahora entrega el estado de Metro y recomienda revisar Waze/Google Maps para auto. Para tiempos reales Providencia -> La Cisterna se puede conectar después una API como Google Maps Distance Matrix o similar.
