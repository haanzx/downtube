from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from downtube.api import api_router
from downtube.config import settings
from downtube.db.session import init_db
from downtube.worker.queue_processor import processor


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    await init_db()
    await processor.start()
    yield
    await processor.stop()


app = FastAPI(title="DownTube", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api")

_dist = settings.frontend_dist


@app.get("/{full_path:path}")
async def spa(full_path: str):
    """Serve the built SPA, falling back to index.html for client routing."""
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    if _dist.exists():
        dist_resolved = _dist.resolve()
        candidate = (dist_resolved / full_path).resolve()
        if candidate.is_file() and str(candidate).startswith(str(dist_resolved)):
            return FileResponse(candidate)
        index = dist_resolved / "index.html"
        if index.exists():
            return FileResponse(index)
    return JSONResponse(
        status_code=200,
        content={
            "detail": "Frontend not built yet. Run `npm run build` in frontend/ "
            "and reload."
        },
    )
