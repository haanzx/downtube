from fastapi import APIRouter

from downtube.api import (
    downloads,
    health,
    library,
    playlists,
    preview,
    search,
    settings,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(downloads.router)
api_router.include_router(search.router)
api_router.include_router(preview.router)
api_router.include_router(library.router)
api_router.include_router(playlists.router)
api_router.include_router(settings.router)
