# Asistente Personal por WhatsApp

Bot personal conectado a WhatsApp Cloud API.

## Comandos

- `metro`: reporte de movilidad con estado de lineas desde `https://www.metro.cl/el-viaje/estado-red`.
- `salir`: modo traslado con Metro, restriccion y recomendaciones.
- `restriccion`: revisa tus dos autos con sello verde y avisa si tienen restriccion normal.
- `restriccion manana`: revisa la restriccion para el dia siguiente.
- `correo`: resumen de correos recientes relevantes.
- `pendientes`: posibles correos que requieren accion.
- `agenda`: agenda manual guardada en la conversacion.
- `agenda <texto>`: agrega un punto a la agenda manual.
- `checklist`: checklist laboral rapido.
- `nota <texto>`: agrega una nota a tu bitacora.
- `bitacora`: muestra notas recientes.
- `gotas`: muestra confirmaciones de gotas registradas.
- `si gotas` / `no gotas`: registra el estado de las gotas.
- `noticias`: titulares recientes sobre municipalismo, municipios y gestion local.
- `linkedin`: propuesta diaria de publicacion sobre municipalismo.
- `post <tema>`: borrador LinkedIn sobre el tema que indiques.
- `mas tecnico`, `mas politico`, `mas breve`, `con datos`: ajusta el ultimo borrador.
- `publicar`: publica en LinkedIn el ultimo borrador revisado.
- `minuta <texto>`: convierte texto largo en minuta ejecutiva.
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

El codigo incluye tareas para enviar mensajes programados:

- `0800-briefing`: clima en Providencia y La Cisterna, restriccion vehicular y Metro.
- `eye-drops-morning`: recordatorio de gotas a las 09:00.
- `1830-metro`: estado de Metro a las 18:30.
- `eye-drops-night`: recordatorio de gotas a las 21:00.
- `linkedin-ideas`: propuesta de publicacion LinkedIn.

En AWS Lambda conviene ejecutarlas con EventBridge Scheduler, invocando `lambda_handler.handler` con un evento como este:

```json
{
  "task": "0800-briefing",
  "secret": "EL_MISMO_TASK_SECRET"
}
```

Importante: WhatsApp Cloud API puede exigir plantillas aprobadas por Meta para mensajes iniciados por el bot fuera de la ventana de conversacion. Si el envio programado falla por politica de WhatsApp, hay que crear templates aprobados o mantener la interaccion dentro de la ventana permitida.

## Restriccion Vehicular

La regla configurada cubre el calendario normal de invierno para vehiculos con sello verde inscritos antes del 1 de septiembre de 2011:

- lunes: 8 y 9
- martes: 0 y 1
- miercoles: 2 y 3
- jueves: 4 y 5
- viernes: 6 y 7

Horario normal: 07:30 a 21:00, de mayo a agosto. En episodios ambientales la autoridad puede ampliar restricciones, por lo que esa parte requiere una fuente oficial adicional.

## Publicar en LinkedIn

1. En LinkedIn Developer Portal, agrega el producto `Share on LinkedIn`.
2. En `Auth`, deja esta URL autorizada:

```text
https://i4p7wvgqyivpri7ysmcjcwweoe0uoekj.lambda-url.us-east-1.on.aws/linkedin/callback
```

3. Guarda `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_REDIRECT_URI` y `LINKEDIN_STATE_SECRET` en variables de entorno de Lambda.
4. Despliega el codigo y abre:

```text
https://i4p7wvgqyivpri7ysmcjcwweoe0uoekj.lambda-url.us-east-1.on.aws/linkedin/login
```

5. Al volver desde LinkedIn, el callback mostrara `LINKEDIN_ACCESS_TOKEN` y `LINKEDIN_PERSON_URN`. Copialos a las variables de entorno de Lambda para que la conexion quede estable.
6. En WhatsApp escribe `post <tema>` y, si te gusta el texto, responde `publicar`.

## Gmail Solo Lectura

1. En Google Cloud Console crea un OAuth Client ID tipo Web application.
2. Agrega esta redirect URI autorizada:

```text
https://i4p7wvgqyivpri7ysmcjcwweoe0uoekj.lambda-url.us-east-1.on.aws/gmail/callback
```

3. Guarda `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` y `GOOGLE_STATE_SECRET` en Lambda.
4. Abre:

```text
https://i4p7wvgqyivpri7ysmcjcwweoe0uoekj.lambda-url.us-east-1.on.aws/gmail/login
```

5. Al volver desde Google, copia `GMAIL_REFRESH_TOKEN` a Lambda.
6. En WhatsApp escribe `correo` o `pendientes`.

Nota: la bitacora, agenda manual y confirmaciones quedan en memoria en esta primera version. Para hacerlas persistentes entre reinicios de Lambda, usar DynamoDB.
