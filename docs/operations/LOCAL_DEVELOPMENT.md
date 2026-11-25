# Desarrollo local

## Requisitos
- Docker Engine o Docker Desktop con Docker Compose v2.
- Git.
- Navegador web moderno.

No es necesario instalar Python, Node.js, PostgreSQL ni Redis en el host para levantar el entorno Compose.

## Inicio
Desde la raíz del repositorio:

```bash
cp .env.example .env
docker compose up --build
```

En Windows PowerShell:
```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Servicios
| Servicio | URL / acceso | Función |
|---|---|---|
| Web | http://localhost:5173 | Interfaz React/Vite |
| API | http://localhost:8000 | API FastAPI |
| OpenAPI | http://localhost:8000/docs | Documentación interactiva |
| PostgreSQL | Red interna `db:5432` | Persistencia |
| Redis | Red interna `redis:6379` | Infraestructura y comprobación de disponibilidad |

PostgreSQL y Redis no publican puertos en el host.

## Comprobaciones
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/ready
docker compose ps
```

La migración inicial se ejecuta al iniciar el contenedor API mediante `alembic upgrade head`.

## Detener
```bash
docker compose down
```

Para eliminar también los datos persistidos de desarrollo:
```bash
docker compose down -v
```
El segundo comando es destructivo para los volúmenes locales.

## Variables de entorno
Copiar `.env.example` a `.env` y ajustar los valores para desarrollo. Los valores de ejemplo son exclusivamente locales y deben rechazarse en producción. No subir `.env` al repositorio.

## Desarrollo sin Compose
Backend: desde `apps/api`, crear un entorno virtual e instalar `pip install -e ".[dev]"`; configurar `DATABASE_URL`, `REDIS_URL` y `CORS_ORIGINS`; ejecutar `alembic upgrade head`, `uvicorn app.main:app --reload` y `pytest`.

Frontend: desde `apps/web`, ejecutar `npm install`, configurar `VITE_API_BASE_URL` y ejecutar `npm run dev` o `npm run build`.
