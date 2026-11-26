from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.profiles import router as profiles_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.middleware("http")
async def prevent_auth_response_caching(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/api/v1/auth/", "/api/v1/profile/")):
        response.headers["Cache-Control"] = "no-store"
    if request.url.path.startswith("/api/v1/profile/"):
        response.headers["Vary"] = "Cookie"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(profiles_router)
