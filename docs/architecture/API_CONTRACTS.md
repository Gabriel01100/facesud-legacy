# Contratos de API — FaceSud

## Convenciones
- Base path: /api/v1.
- Transporte: HTTP; JSON para respuestas.
- OpenAPI: /docs y /openapi.json.
- Rutas autenticadas: cookies de sesión opacas; no se aceptan tokens Bearer para la aplicación web.
- Todas las respuestas de /api/v1/auth/* llevan Cache-Control: no-store, incluso errores de autenticación.
- Los endpoints de perfiles también usan Cache-Control: no-store y Vary: Cookie.

## Salud
### GET /api/v1/health
Comprueba que el proceso HTTP responde. Respuesta HTTP 200: {"status":"ok"}.

### GET /api/v1/health/ready
Comprueba PostgreSQL mediante SELECT 1 y Redis mediante PING. Respuesta HTTP 200: {"status":"ready","postgres":"ok","redis":"ok"}.

## Identity

### POST /api/v1/auth/register
Requiere Origin permitido. Recibe email válido y password de al menos 12 caracteres. Crea cuenta PENDING_EMAIL y envía enlace. HTTP 202 genérico. SMTP no configurado: HTTP 503 sin crear cuenta.

### POST /api/v1/auth/email-verification/verify
Requiere Origin permitido. Token válido, no vencido y no usado activa la cuenta. HTTP 200; no inicia sesión. Token inválido/vencido/usado: HTTP 400 genérico.

### POST /api/v1/auth/email-verification/resend
Requiere Origin permitido. Recibe email; invalida tokens anteriores y envía uno nuevo solo para cuentas pendientes. HTTP 202 genérico.

### POST /api/v1/auth/login
Requiere Origin permitido. Autentica cuenta activa por correo/contraseña.

Request: {"email":"persona@example.com","password":"contraseña"}

Respuesta HTTP 200: {"id":"uuid","email":"persona@example.com","csrf_token":"token-aleatorio"}.

Límite inicial:
- Máximo 5 intentos en 15 minutos por combinación IP + correo.
- Máximo 30 intentos en 15 minutos por IP.
- Exceso: HTTP 429 y encabezado Retry-After.
- Un login exitoso limpia los buckets IP+correo e IP.
- Las claves de bucket se almacenan como SHA-256 en PostgreSQL.

Un login exitoso revoca la sesión asociada a la cookie entrante (si existe) antes de crear la nueva.

Cookie:
- facesud_session en development/test.
- __Host-facesud_session en cualquier otro entorno.
- HttpOnly, SameSite=Lax, Path=/, sin Domain.
- Secure en cualquier entorno distinto de development/test.

El token CSRF se devuelve en JSON y solo su hash se guarda en PostgreSQL. El cliente lo conserva en memoria y lo envía como X-CSRF-Token.

Credenciales incorrectas, cuenta inexistente o cuenta no activa: HTTP 401 genérico. Cuenta pendiente no puede iniciar sesión.

### POST /api/v1/auth/password-reset/request
Requiere Origin permitido. Recibe email y devuelve HTTP 202 con respuesta genérica, independientemente de si existe una cuenta activa. Si corresponde, envía un token opaco de un solo uso con TTL de 30 minutos. Rate limit: 3 por hora por IP+correo y 10 por hora por IP.

### POST /api/v1/auth/password-reset/confirm
Requiere Origin permitido. Recibe token y new_password (mínimo 12 caracteres). Token válido actualiza la credencial, invalida tokens de recuperación pendientes y revoca todas las sesiones. Token inválido, vencido o usado: HTTP 400 genérico.

### POST /api/v1/auth/password/change
Requiere sesión válida, Origin permitido, CSRF y contraseña actual. Recibe current_password y new_password (mínimo 12 caracteres). Límite: 5 intentos/15 minutos por IP+correo y 20/15 minutos por IP. Actualiza la credencial, invalida tokens de recuperación pendientes y revoca todas las sesiones; devuelve HTTP 204 y elimina la cookie actual.

### GET /api/v1/auth/me
Requiere sesión válida; devuelve UUID y correo normalizado. last_seen_at se persiste como máximo una vez por minuto.

### POST /api/v1/auth/csrf
Requiere sesión y Origin permitido. Rota el token CSRF y devuelve el valor nuevo. Cache-Control: no-store.

### POST /api/v1/auth/logout
Requiere Origin permitido. Si la sesión sigue activa, exige X-CSRF-Token válido. Si no hay sesión vigente o ya venció, devuelve igualmente HTTP 204. Siempre elimina la cookie cuando la solicitud tiene Origin permitido. Una sesión activa con CSRF incorrecto devuelve 403 y no revoca la sesión.

## Profiles

Los perfiles se consultan exclusivamente por el titular en esta etapa, conforme a D-023. No existen rutas por ID, username, listados, búsquedas ni directorios.

### GET /api/v1/profile/me
Requiere sesión válida. Devuelve el perfil propio o valores vacíos si todavía no se guardó información. No crea un registro de perfil al consultar.

Campos de respuesta permitidos:
- display_name: nombre visible o null.
- username: identificador normalizado sin @ o null.
- bio: biografía o null.
- account_created_at: fecha de creación derivada de Identity.Account; solo lectura.
- avatar_url: null hasta implementar almacenamiento protegido de fotografías.
- community_unit: objeto con name y kind derivado exclusivamente de la vinculación aprobada propia; null cuando no existe una vinculación aprobada. No es editable desde Profiles.

Respuesta privada: Cache-Control: no-store y Vary: Cookie.

### PATCH /api/v1/profile/me
Requiere sesión válida, Origin permitido y X-CSRF-Token válido. Solo admite display_name, username y bio; los campos desconocidos se rechazan.

Validaciones:
- display_name: 2 a 60 caracteres después de normalizar espacios; null permite dejarlo sin configurar.
- username: 3 a 24 caracteres ASCII entre letras, números y guion bajo; se normaliza a minúsculas y se acepta un @ inicial opcional. Debe ser único; conflicto: HTTP 409 genérico.
- bio: máximo 280 caracteres; null permite limpiarla.
- Debe enviarse al menos un campo.
- No se aceptan avatar_url, account_created_at, community_unit, account_id ni campos internos.

La fila de perfil se crea al guardar por primera vez. La unicidad se garantiza también mediante restricción de base de datos. Respuesta limitada a los campos permitidos indicados en GET.

No se implementan perfiles ajenos ni se interpreta autenticación como aprobación de vinculación comunitaria. La unidad comunitaria no puede editarse desde este endpoint.

## Community

Las rutas de Community aplican `Cache-Control: no-store` y `Vary: Cookie` cuando corresponda. Las operaciones mutables requieren sesión, Origin permitido y CSRF.

### GET /api/v1/community/units
Lista unidades activas disponibles. No expone cuentas ni vinculaciones.

### POST /api/v1/community/units
Solo cuentas cuyo correo figure en `COMMUNITY_REVIEWER_EMAILS` pueden crear unidades. Request: `name`, `unit_type` (branch/ward/stake), `country_code` ISO alpha-2, y ubicación opcional. Una unidad hija solo puede tener como padre una unidad compatible del mismo país. No hay borrado físico ni edición pública de unidades.

### POST /api/v1/community/membership-requests
Requiere sesión y CSRF. Request: `unit_id`. Solo cuentas activas pueden solicitar. Se permite una solicitud pendiente por cuenta y una vinculación aprobada por cuenta. La respuesta marca `provisional: true`; no se solicita ni almacena cédula ni documentos.

### GET /api/v1/community/membership/me
Devuelve únicamente el historial de vinculaciones de la cuenta autenticada.

### GET /api/v1/community/review/requests
Solo revisores configurados en `COMMUNITY_REVIEWER_EMAILS`. Devuelve hasta 100 solicitudes pendientes con correo de referencia y unidad. No expone notas internas ni IDs de revisor.

### POST /api/v1/community/review/requests/{request_id}
Solo revisores con sesión y CSRF. Acepta `decision` approved/rejected y nota interna opcional. Registra reviewer y fecha. Una aprobación es administrativa y provisional, no una verificación institucional.

La asignación de revisores se controla por configuración de entorno, nunca por datos enviados por el cliente. En Compose local se configura `COMMUNITY_REVIEWER_EMAILS` con correos de cuentas previamente registradas y verificadas. Mantener la variable vacía por defecto.

## Social

Las rutas sociales aplican `Cache-Control: no-store` y `Vary: Cookie`. La elegibilidad se valida en backend: la cuenta debe estar activa y tener una vinculación comunitaria aprobada.

### GET /api/v1/social/feed
Requiere sesión y vinculación aprobada. Devuelve publicaciones cronológicas descendentes de la misma unidad aprobada del lector. Query: `limit` (1-50, default 20), `before` y `before_id` (cursor compuesto, ambos obligatorios si se pagina). La consulta excluye autores inactivos o sin vinculación aprobada vigente en esa unidad. La respuesta solo expone UUID de publicación, texto, fecha, nombre visible/username opcionales y `is_mine`; nunca correo ni UUID de cuenta del autor. HTTP 403 cuando no existe vinculación aprobada. Respuesta privada no cacheable.

### POST /api/v1/social/posts
Requiere sesión, Origin permitido y CSRF. Recibe `{"body":"texto"}`; texto normalizado, no vacío, máximo 2.000 caracteres. La unidad se deriva exclusivamente de la vinculación aprobada del autor en el servidor. HTTP 201. Sin vinculación aprobada: HTTP 403.

### DELETE /api/v1/social/posts/{post_id}
Requiere sesión, Origin permitido y CSRF. Solo permite eliminar publicaciones propias; publicaciones ajenas e inexistentes responden HTTP 404 para no revelar su existencia. HTTP 204 al eliminar.

La primera entrega no incorpora imágenes, comentarios, reacciones, edición de publicaciones, perfiles ajenos ni búsquedas.

## Política de sesiones
- Expiración absoluta: 7 días.
- Inactividad: 30 minutos.
- Máximo: 5 sesiones activas por cuenta; al crear una sexta se revoca la más antigua.
- PostgreSQL almacena hashes de sesión y CSRF.
- El límite de 5 sesiones se valida bajo bloqueo de fila de cuenta; una prueba concurrente PostgreSQL cubre creación paralela.
- La fila de cuenta se bloquea y revalida al crear sesión, después de verificar Argon2.
- Redis no almacena sesiones ni rate limits.

## CSRF y navegador
Las operaciones mutables validan Origin y CSRF. Ante 403 con detalle CSRF validation failed, el cliente solicita un token nuevo y reintenta la solicitud una sola vez. El reintento debe usar un cuerpo reproducible.

## Correo
El transporte es SMTP configurable y compartido por verificación de correo y recuperación de contraseña. Variables: SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_STARTTLS, EMAIL_FROM, FRONTEND_BASE_URL. Registro y recuperación devuelven HTTP 503 si falta configuración.

En desarrollo Compose, Mailpit captura correos en `mailpit:1025`, sin TLS ni autenticación; su UI se publica únicamente en `127.0.0.1:8025`. En producción se exige SMTP autenticado con STARTTLS y credenciales reales. El proveedor sugerido es Resend mediante SMTP; requiere dominio emisor verificado y registros DNS de autenticación. Mailpit nunca debe usarse como proveedor de producción.

Las direcciones se normalizan en NFC y se validan con email-validator antes de persistir; se conserva el comportamiento case-insensitive vigente.

## Limpieza de Identity
Ejecutar python -m app.identity.cleanup periódicamente. El comando elimina sesiones revocadas, vencidas por TTL absoluto o inactivas por más de 30 minutos; tokens de verificación/recuperación usados o vencidos con más de 7 días; y buckets antiguos de login, registro, reenvío y recuperación. Programación sugerida: cada hora mediante cron/scheduler externo.

## Producción
REDIS_URL debe contener contraseña; REDIS_PASSWORD protege el servicio Redis en Compose. Los valores secretos se inyectan desde el entorno/secret manager.

## Pendientes
- Google OpenID Connect y vinculación explícita.
- Almacenamiento protegido, validación y entrega de fotografías de perfil.
- Verificación institucional de membresía, pendiente de procedimiento y datos autorizados.
- Cuenta y dominio emisor verificado del proveedor SMTP transaccional; credenciales, SPF, DKIM y DMARC.
- Pruebas E2E de navegador para registro, verificación, login, logout, recuperación, cambio de contraseña y CSRF multi-pestaña.
- Pruebas de concurrencia del rate limiting y carga sostenida.
- Revisión de umbrales de rate limiting y retención de tokens con métricas/política de privacidad.

La elegibilidad comunitaria por cédula de miembro es independiente de la autenticación. Google o contraseña no acreditan membresía. No se solicita ni almacena el número de cédula en esta etapa.
