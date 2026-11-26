# Contratos de API — FaceSud

## Convenciones
- Base path: /api/v1.
- Transporte: HTTP; JSON para respuestas.
- La documentación OpenAPI es generada por FastAPI en /docs y /openapi.json.
- Los errores usan el formato estándar de FastAPI.
- Las rutas autenticadas usan cookies de sesión opacas; no se aceptan tokens Bearer para la aplicación web.

## Salud

### GET /api/v1/health
Comprueba que el proceso HTTP de la API responde. No verifica dependencias externas.

Respuesta HTTP 200: {"status":"ok"}

### GET /api/v1/health/ready
Comprueba conectividad con PostgreSQL mediante SELECT 1 y con Redis mediante PING.

Respuesta HTTP 200: {"status":"ready","postgres":"ok","redis":"ok"}

## Identity

### POST /api/v1/auth/register
Requiere Origin permitido. Recibe email y password (mínimo 12 caracteres). Crea una cuenta PENDING_EMAIL y envía un enlace de verificación. Devuelve HTTP 202 con un mensaje genérico que no confirma si la dirección ya existe. Si SMTP no está configurado, devuelve HTTP 503 sin crear la cuenta.

### POST /api/v1/auth/email-verification/verify
Requiere Origin permitido. Recibe token; un token válido, no vencido y no utilizado activa la cuenta. Devuelve HTTP 200. No inicia sesión automáticamente. Token inválido, vencido o usado: HTTP 400 con mensaje genérico.

### POST /api/v1/auth/email-verification/resend
Requiere Origin permitido. Recibe email; invalida enlaces anteriores y envía uno nuevo solo si existe una cuenta pendiente. Devuelve HTTP 202 con mensaje genérico, independientemente de que exista la cuenta.

### POST /api/v1/auth/login
Autentica una cuenta activa mediante email y contraseña. Requiere un encabezado Origin que coincida exactamente con un elemento de CORS_ORIGINS.

Request: {"email":"persona@example.com","password":"contraseña"}

Respuesta HTTP 200: {"id":"uuid","email":"persona@example.com","csrf_token":"token-aleatorio"}

Establece una única cookie:
- facesud_session en desarrollo o __Host-facesud_session en producción: HttpOnly, SameSite=Lax, Path=/, sin Domain; Secure en producción.

El token CSRF se devuelve en el cuerpo de la respuesta y su hash se guarda en PostgreSQL. El frontend debe conservarlo en memoria y enviarlo como encabezado X-CSRF-Token en operaciones mutables. Las respuestas de autenticación llevan Cache-Control: no-store.

Credenciales incorrectas, cuenta inexistente o cuenta no activa producen el mismo error HTTP 401. Una cuenta pendiente de verificación no puede iniciar sesión.

### GET /api/v1/auth/me
Requiere una cookie de sesión válida. Devuelve el UUID y el email normalizado de la cuenta autenticada. Cada solicitud autenticada válida actualiza last_seen_at.

### POST /api/v1/auth/csrf
Requiere cookie de sesión y Origin permitido. Rota el token CSRF, persiste su hash y devuelve el nuevo token. Se utiliza al recargar la aplicación para obtener un token CSRF nuevo sin exponer la cookie HttpOnly. Respuesta Cache-Control: no-store.

### POST /api/v1/auth/logout
Requiere Origin permitido, cookie de sesión y encabezado X-CSRF-Token válido contra el hash guardado en PostgreSQL. Revoca la sesión actual y elimina la cookie de sesión. Respuesta HTTP 204.

## Política de sesiones
- Expiración absoluta: 7 días desde la creación.
- Expiración por inactividad: 30 minutos.
- Máximo: 5 sesiones activas por cuenta.
- Al emitir una sexta sesión, se revoca la sesión activa más antigua.
- PostgreSQL almacena hashes de tokens de sesión y CSRF, nunca los valores originales.
- Redis no se utiliza para sesiones.

## CORS y seguridad del navegador
En desarrollo se permite el origen configurado en CORS_ORIGINS (por defecto http://localhost:5173). CORS habilita credenciales solo para esa lista explícita; no se permite wildcard con credenciales. Producción requiere orígenes HTTPS explícitos.

Las operaciones mutables deben validar Origin y CSRF. El token CSRF viaja en un encabezado personalizado y no se envía automáticamente por el navegador. SameSite no se considera la única defensa.

## Configuración de correo
El adaptador SMTP utiliza STARTTLS con validación de certificados. Variables: SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, FRONTEND_BASE_URL. El registro se deshabilita con HTTP 503 cuando no existe configuración de correo.

## Pendientes
- Recuperación y cambio de contraseña.
- Inicio/callback Google OpenID Connect y vinculación explícita.
- Rate limiting de login, registro y reenvío.
- Frontend de autenticación y pruebas E2E.
- Política de revocación ante cambio de contraseña/eventos de seguridad.
- Pruebas de concurrencia PostgreSQL.

La elegibilidad comunitaria por cédula de miembro es una verificación separada de identidad y autenticación. La autenticación de Google o por contraseña no acredita membresía. No se solicita ni almacena el número de cédula en esta etapa.
