from fastapi import APIRouter, HTTPException, Query

from downtube.services.search import _fetch_url_metadata, _is_url

router = APIRouter(prefix="/preview", tags=["preview"])


@router.get("")
async def preview(url: str = Query(..., min_length=1)) -> dict:
    """Fetch metadata for a URL without enqueuing a download."""
    if not _is_url(url):
        raise HTTPException(status_code=400, detail="Input bukan URL yang valid")
    meta = await _fetch_url_metadata(url)
    if not meta:
        raise HTTPException(status_code=404, detail="Tidak dapat mengambil metadata dari URL ini")
    return meta
