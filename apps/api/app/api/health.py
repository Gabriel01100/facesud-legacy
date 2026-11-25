from fastapi import APIRouter, HTTPException, status

from app.core.cache import check_redis
from app.core.database import check_database

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness() -> dict[str, str]:
    database_ok = check_database()
    redis_ok = check_redis()
    if not database_ok or not redis_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unavailable",
                "postgres": "ok" if database_ok else "unavailable",
                "redis": "ok" if redis_ok else "unavailable",
            },
        )
    return {"status": "ready", "postgres": "ok", "redis": "ok"}
