# Contratos de API — FaceSud

## Convenciones
- Base path: /api/v1.
- Transporte: HTTP; JSON para respuestas.
- OpenAPI: /docs y /openapi.json.
- Rutas autenticadas: cookies de sesión opacas; no se aceptan tokens Bearer para la aplicación web.
- Todas las respuestas de /api/v1/auth/* llevan Cache-Control: no-store, incluso errores de autenticación.

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
SMTP STARTTLS con validación TLS. Variables: SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, FRONTEND_BASE_URL. Registro y recuperación deshabilitados con HTTP 503 si no hay configuración. El proveedor SMTP/API definitivo, SPF, DKIM y DMARC siguen pendientes.

Las direcciones se normalizan en NFC y se validan con email-validator antes de persistir; se conserva el comportamiento case-insensitive vigente.

## Limpieza de Identity
Ejecutar python -m app.identity.cleanup periódicamente. El comando elimina sesiones revocadas, vencidas por TTL absoluto o inactivas por más de 30 minutos; tokens de verificación/recuperación usados o vencidos con más de 7 días; y buckets antiguos de login, registro, reenvío y recuperación. Programación sugerida: cada hora mediante cron/scheduler externo.

## Producción
REDIS_URL debe contener contraseña; REDIS_PASSWORD protege el servicio Redis en Compose. Los valores secretos se inyectan desde el entorno/secret manager.

## Pendientes
- Google OpenID Connect y vinculación explícita.
- Proveedor transaccional definitivo, credenciales y configuración SPF/DKIM/DMARC.
- Pruebas E2E de navegador para registro, verificación, login, logout, recuperación, cambio de contraseña y CSRF multi-pestaña.
- Pruebas de concurrencia del rate limiting y carga sostenida.
- Revisión de umbrales de rate limiting y retención de tokens con métricas/política de privacidad.

La elegibilidad comunitaria por cédula de miembro es independiente de la autenticación. Google o contraseña no acreditan membresía. No se solicita ni almacena el número de cédula en esta etapa.
