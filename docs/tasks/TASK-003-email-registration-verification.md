# TASK-003 — Registro y verificación de correo

## Objetivo
Permitir el alta de cuentas locales sin habilitarlas hasta que la persona demuestre control de la dirección de correo.

## Decisiones de implementación
- El envío se realiza mediante SMTP con STARTTLS y validación TLS del certificado.
- El proveedor queda desacoplado de los casos de uso: se puede reemplazar por un adaptador de API transaccional sin cambiar el modelo ni los endpoints.
- No se habilita un servidor SMTP falso ni se registra el token en logs.
- El registro requiere configuración de correo; si no está configurado, responde HTTP 503 antes de crear una cuenta.
- Los enlaces de verificación vencen a las 24 horas.
- Los tokens son aleatorios, de un solo uso; PostgreSQL almacena únicamente SHA-256 del token.
- Reenviar un enlace invalida todos los tokens anteriores que aún no se usaron.
- La respuesta de registro y reenvío no revela si una dirección ya existe.
- Verificar el correo activa la cuenta, pero no inicia sesión automáticamente.
- El correo normalizado sigue el criterio actual de normalize_email; su política definitiva queda pendiente.
- No se realiza verificación de membresía ni se solicita/almacena el número de cédula.

## Endpoints
- POST /api/v1/auth/register
- POST /api/v1/auth/email-verification/verify
- POST /api/v1/auth/email-verification/resend

## Persistencia
La migración 0003_email_verification crea identity_email_verification_tokens, con hash único, fecha de expiración, fecha de uso y FK a la cuenta.

## Seguridad
- Contraseña hasheada con Argon2.
- Token de verificación nunca se persiste en texto plano.
- Cuenta permanece PENDING_EMAIL hasta verificar.
- Token expirado o usado se rechaza.
- Operaciones POST validan Origin permitido.
- Respuestas de registro y verificación incluyen Cache-Control: no-store.
- El envío SMTP ocurre después del commit; un fallo no elimina la cuenta pendiente y se puede solicitar reenvío.
- El registro no se considera listo para exposición pública: rate limiting de login/registro, monitoreo de abuso y pruebas de concurrencia PostgreSQL siguen pendientes.

## Configuración
Variables: SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, FRONTEND_BASE_URL.

El adaptador utiliza SMTP STARTTLS (habitualmente puerto 587). El secreto SMTP debe inyectarse mediante variables de entorno/secret manager y nunca versionarse.

## Pruebas
La suite de integración cubre registro, bloqueo de login previo a verificación, activación, vencimiento, uso único, invalidación de tokens anteriores y validación de Origin.
