# Contratos de API — FaceSud

## Convenciones
- Base path: `/api/v1`.
- Transporte: HTTP; JSON para respuestas.
- La documentación OpenAPI es generada por FastAPI en `/docs` y `/openapi.json`.
- Los errores usan el formato estándar de FastAPI.
- Las rutas autenticadas usan cookies de sesión opacas; no se aceptan tokens Bearer para la aplicación web.

## Salud

### GET /api/v1/health
Comprueba que el proceso HTTP de la API responde. No verifica dependencias externas.

Respuesta HTTP 200:
```json
{"status":"ok"}
```

### GET /api/v1/health/ready
Comprueba conectividad con PostgreSQL mediante `SELECT 1` y con Redis mediante `PING`.

Respuesta HTTP 200:
```json
{"status":"ready","postgres":"ok","redis":"ok"}
```

Respuesta HTTP 503 si una o ambas dependencias no están disponibles:
```json
{
  "detail": {
    "status": "unavailable",
    "postgres": "ok",
    "redis": "unavailable"
  }
}
```

## Identity — endpoints implementados en esta subetapa

### POST /api/v1/auth/login
Autentica una cuenta activa mediante email y contraseña. Requiere un encabezado `Origin` que coincida exactamente con un elemento de `CORS_ORIGINS`.

Request:
```json
{"email":"persona@example.com","password":"contraseña"}
```

Respuesta HTTP 200:
```json
{"id":"uuid","email":"persona@example.com"}
```

Establece dos cookies:
- `facesud_session` en desarrollo o `__Host-facesud_session` en producción: HttpOnly, SameSite=Lax, Path=/, sin Domain; Secure en producción.
- `facesud_csrf`: mismo alcance y flags de transporte, pero no HttpOnly para que el cliente pueda copiarlo al encabezado `X-CSRF-Token`.

Credenciales incorrectas, cuenta inexistente o cuenta no activa producen el mismo error HTTP 401. Una cuenta pendiente de verificación no puede iniciar sesión.

### GET /api/v1/auth/me
Requiere una cookie de sesión válida. Devuelve el UUID y el email normalizado de la cuenta autenticada. Cada solicitud autenticada válida actualiza `last_seen_at`.

### POST /api/v1/auth/logout
Requiere Origin permitido, cookie de sesión, cookie CSRF y encabezado `X-CSRF-Token` coincidente con la cookie y con el hash guardado en PostgreSQL. Revoca la sesión actual y elimina ambas cookies. Respuesta HTTP 204.

## Política de sesiones
- Expiración absoluta: 7 días desde la creación.
- Expiración por inactividad: 30 minutos.
- Máximo: 5 sesiones activas por cuenta.
- Al emitir una sexta sesión, se revoca la sesión activa más antigua.
- PostgreSQL almacena hashes de tokens, nunca los valores originales.
- Redis no se utiliza para sesiones.

## CORS y seguridad del navegador
En desarrollo se permite el origen configurado en `CORS_ORIGINS` (por defecto `http://localhost:5173`). CORS habilita credenciales solo para esa lista explícita; no se permite wildcard con credenciales. Producción requiere orígenes HTTPS explícitos.

Las operaciones mutables deben validar Origin y CSRF. SameSite no se considera la única defensa.

## Contratos pendientes
- Registro de cuenta y verificación de correo (requiere proveedor transaccional).
- Recuperación y cambio de contraseña.
- Inicio/callback Google OpenID Connect y vinculación explícita.
- Revocación de sesiones/dispositivos.
- Rate limiting de login y registro.
- Frontend de autenticación y E2E.

La elegibilidad comunitaria por cédula de miembro es una verificación separada de identidad y autenticación. La autenticación de Google o por contraseña no acredita membresía. No se solicita ni almacena el número de cédula en esta etapa.

Los detalles pendientes se encuentran en [OPEN_DECISIONS.md](../decisions/OPEN_DECISIONS.md).
