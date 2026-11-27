from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.community import router as community_router
from app.api.health import router as health_router
from app.api.media import router as media_router
from app.api.posts import router as posts_router
from app.api.interactions import router as interactions_router
from app.api.profiles import router as profiles_router
from app.core.config import settings
from app.models import comment as comment_models, community as community_models, media as media_models, post as post_models, reaction as reaction_models  # noqa: F401 — register domain tables

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.middleware("http")
async def prevent_private_response_caching(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith((
        "/api/v1/auth/", "/api/v1/profile/", "/api/v1/community/", "/api/v1/social/"
    )):
        if not response.headers.get("Cache-Control"):
            response.headers["Cache-Control"] = "no-store"
    if request.url.path.startswith((
        "/api/v1/profile/", "/api/v1/community/", "/api/v1/social/"
    )):
        vary = response.headers.get("Vary")
        response.headers["Vary"] = f"{vary}, Cookie" if vary and "cookie" not in vary.lower() else (vary or "Cookie")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(community_router)
app.include_router(posts_router)
app.include_router(media_router)
app.include_router(interactions_router)
