from fastapi import APIRouter, HTTPException, Query

from downtube.services import search as search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1),
    type: str = "song",
    limit: int = 20,
) -> list[dict]:
    try:
        return await search_service.search(q, type, limit)
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="search not implemented yet (P2)")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"search error: {exc}")
