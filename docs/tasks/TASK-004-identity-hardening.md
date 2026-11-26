# TASK-004 — Endurecimiento de Identity y CI

## Alcance implementado
- Un login exitoso revoca la sesión asociada a la cookie entrante antes de emitir una nueva.
- Logout devuelve 204 y limpia la cookie cuando no existe sesión vigente o ya venció. Si existe sesión activa, sigue exigiendo Origin permitido y CSRF válido.
- Cookies Secure y prefijo __Host- en todo entorno salvo development y test.
- Tests HTTP de autenticación y registro ejecutables contra PostgreSQL mediante IDENTITY_TEST_DATABASE_URL; SQLite queda como fallback local y para pruebas unitarias.
- Rate limiting de login persistido en PostgreSQL: 5 intentos por 15 minutos por combinación IP/correo y 30 por IP en 15 minutos. Ventana fija, respuesta 429 y Retry-After. Un login exitoso limpia ambos buckets.
- Rate limiting de registro: 2 intentos por hora por IP/correo y 5 por hora por IP. Reenvío de verificación: 3 por hora por IP/correo y 10 por hora por IP. Recuperación: 3 por hora por IP/correo y 10 por IP. Cambio autenticado: 5 por 15 minutos por IP/correo y 20 por IP. Los buckets usan claves hash y scopes separados; ver D-021 y D-022.
- La autenticación no bloquea la fila de cuenta mientras calcula Argon2. create_session toma el bloqueo y vuelve a comprobar que la cuenta exista y siga ACTIVE.
- En producción, REDIS_URL debe contener contraseña.
- Cliente frontend exporta authenticatedFetch: ante 403 específico de CSRF, solicita token nuevo y reintenta una sola vez.
- Cache-Control: no-store para todas las respuestas bajo /api/v1/auth, incluidos 401.
- last_seen_at se actualiza como máximo una vez por minuto.
- Comando de limpieza: python -m app.identity.cleanup. Elimina sesiones vencidas/revocadas, buckets de rate limiting antiguos y tokens de verificación/recuperación usados o expirados con más de 7 días.
- Normalización NFC y validación de email con email-validator.
- Ruff, escaneo Gitleaks, usuario no privilegiado para la API y tests PostgreSQL en CI.

## Decisión de rate limiting
Se eligió PostgreSQL en lugar de Redis para mantener un único almacenamiento operativo para esta política y evitar incorporar otra dependencia de disponibilidad. Los buckets almacenan hashes SHA-256 de sus claves, no correo ni IP en claro.

Los límites son por IP+correo e IP global, no por correo global: se evita que un tercero bloquee a una víctima atacando su cuenta desde cualquier origen. Los límites iniciales deben observarse con métricas antes de endurecerlos. El proxy inverso debe entregar una IP cliente confiable; no se deben aceptar X-Forwarded-For de clientes arbitrarios.

## Operación
Programar python -m app.identity.cleanup mediante cron o scheduler externo, idealmente cada hora. No se incorpora worker ni scheduler dentro de la API.

En producción definir REDIS_URL con contraseña URL-encoded y la misma contraseña mediante REDIS_PASSWORD.

## Pendientes explícitos
- Interfaz inicial integrada con login, registro, verificación, reenvío, solicitud/restablecimiento de contraseña y cambio autenticado de contraseña. Pendientes pruebas frontend automatizadas y pruebas E2E reales.
- `apps/web/package-lock.json` generado en Node 22/npm 10 y versionado. CI usa `npm ci` con permisos mínimos.
- La imagen de producción del frontend se difiere hasta la etapa de despliegue.
- Se agregaron pruebas concurrentes PostgreSQL para verificar el máximo de 5 sesiones por cuenta y la atomicidad del rate limiting. Sigue pendiente prueba de carga sostenida y E2E de CSRF entre pestañas.


## Recuperación y cambio de contraseña (implementación inicial)
- `POST /api/v1/auth/password-reset/request`: respuesta genérica para no revelar si existe una cuenta; emite token opaco de 30 minutos para cuentas activas.
- `POST /api/v1/auth/password-reset/confirm`: consume token de un solo uso, actualiza Argon2 y revoca todas las sesiones.
- `POST /api/v1/auth/password/change`: exige sesión, Origin, CSRF y contraseña actual; cambia la credencial, invalida tokens pendientes y revoca todas las sesiones.
- El token se almacena solo como SHA-256. Se invalida al solicitar uno nuevo.
- Rate limiting de recuperación: 3 intentos por hora por IP+correo y 10 por IP. Cambio autenticado: 5 intentos por 15 minutos por IP+correo y 20 por IP.
- SMTP STARTTLS reutiliza la configuración existente; no se eligió proveedor definitivo ni se configuraron credenciales reales.
