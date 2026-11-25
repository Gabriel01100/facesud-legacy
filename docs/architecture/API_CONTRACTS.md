# Contratos de API — primera versión ejecutable

## Convenciones
- Base path: `/api/v1`.
- Transporte: HTTP; JSON para respuestas.
- La documentación OpenAPI es generada por FastAPI en `/docs` y `/openapi.json`.
- Los endpoints de esta etapa no reciben datos de usuario ni implementan autenticación.
- Los errores usan el formato estándar de FastAPI. No se define todavía un sobre de error propio.

## Endpoints implementados

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

Los valores de disponibilidad reflejan cada comprobación por separado.

## CORS
En desarrollo se permite el origen configurado en `CORS_ORIGINS` (por defecto `http://localhost:5173`). La lista debe ajustarse explícitamente al desplegar. La autenticación por cookie requerirá habilitar credenciales solo para orígenes explícitamente permitidos; nunca usar wildcard con credenciales.

## Contratos previstos — todavía no implementados
La siguiente etapa incorporará los contratos de Identity. Los nombres y esquemas definitivos se documentarán junto con su implementación y pruebas; no deben tratarse como endpoints disponibles.

- Registro con correo electrónico y contraseña.
- Verificación de correo y activación de cuenta.
- Inicio y cierre de sesión mediante cookie de sesión opaca.
- Consulta del usuario autenticado.
- Inicio y callback de Google OpenID Connect.
- Recuperación y cambio de contraseña.
- Revocación de sesiones.

Las operaciones protegidas por cookie deberán usar protección CSRF y validación de origen. Los secretos OAuth y las contraseñas nunca se enviarán al frontend salvo el formulario de credenciales durante el transporte TLS; las contraseñas se almacenarán únicamente como hashes resistentes a ataques offline. La cookie no será accesible desde JavaScript.

La elegibilidad comunitaria por cédula de miembro no se implementará en esta etapa de autenticación inicial. Se agregará como verificación separada antes de habilitar la participación comunitaria real, una vez definido el procedimiento. La autenticación de Google no reemplaza esa verificación.

Los detalles pendientes se encuentran en [OPEN_DECISIONS.md](../decisions/OPEN_DECISIONS.md).
