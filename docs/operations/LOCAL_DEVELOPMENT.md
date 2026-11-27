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
| Redis | Red interna `redis:6379` | Infraestructura y comprobación de disponibilidad |\n| Imágenes | Volumen Docker `media_data` | Archivos WebP privados de publicaciones |

PostgreSQL y Redis no publican puertos en el host. Las imágenes locales se guardan en `media_data`; `docker compose down` conserva el volumen y `docker compose down -v` también lo elimina.

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

## Administración inicial de Community\n\nPara habilitar revisión comunitaria en desarrollo, agregá en el archivo `.env` el correo de una cuenta que ya hayas registrado y verificado:\n\n```dotenv\nCOMMUNITY_REVIEWER_EMAILS=responsable@tu-correo.com\n```\n\nReiniciá el servicio API. Solo esa cuenta podrá crear unidades y aprobar/rechazar solicitudes. Dejá la variable vacía si todavía no designaste responsables. No uses una dirección compartida ni un correo que no controles.\n\n## Imágenes privadas\n\nEl entorno local usa `MEDIA_STORAGE_BACKEND=local`; no hace falta configurar credenciales. Los archivos se escriben en el volumen Docker `media_data`, no dentro del repositorio ni en `apps/web/public`.\n\nEn producción se requiere un bucket S3-compatible privado con `MEDIA_STORAGE_BACKEND=s3`, `MEDIA_S3_BUCKET`, `MEDIA_S3_REGION`, `MEDIA_S3_ACCESS_KEY_ID` y `MEDIA_S3_SECRET_ACCESS_KEY`. `MEDIA_S3_ENDPOINT_URL` es opcional y, si se usa en producción, debe ser HTTPS. El bucket debe bloquear acceso público y las credenciales deben inyectarse desde un gestor de secretos.\n\nLímites iniciales: 5 MiB por archivo, 20 megapíxeles y cuatro imágenes por publicación. Solo JPEG, PNG y WebP estáticos; el servidor recodifica a WebP y elimina metadatos EXIF.\n\n## Variables de entorno
Copiar `.env.example` a `.env` y ajustar los valores para desarrollo. Los valores de ejemplo son exclusivamente locales y deben rechazarse en producción. No subir `.env` al repositorio.

## Desarrollo sin Compose
Backend: desde `apps/api`, crear un entorno virtual e instalar `pip install -e ".[dev]"`; configurar `DATABASE_URL`, `REDIS_URL` y `CORS_ORIGINS`; ejecutar `alembic upgrade head`, `uvicorn app.main:app --reload` y `pytest`.

Frontend: desde `apps/web`, ejecutar `npm install`, configurar `VITE_API_BASE_URL` y ejecutar `npm run dev` o `npm run build`.
