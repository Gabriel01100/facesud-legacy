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
En desarrollo se permite el origen configurado en `CORS_ORIGINS` (por defecto `http://localhost:5173`). La lista debe ajustarse explícitamente al desplegar. No se habilitan credenciales ni métodos de escritura en esta etapa.

## Evolución
La autenticación web se implementará en una etapa posterior conforme a D-017: cookie de sesión HttpOnly con identificador opaco, sesiones persistidas en PostgreSQL, expiración y revocación del lado servidor, y protección CSRF/origen para operaciones que modifican estado. No se deben implementar tokens de sesión en almacenamiento web accesible a JavaScript.

Los contratos de registro, login, logout, recuperación y verificación de cuenta todavía no están definidos; requieren resolver los puntos de identidad listados en [OPEN_DECISIONS.md](../decisions/OPEN_DECISIONS.md).
