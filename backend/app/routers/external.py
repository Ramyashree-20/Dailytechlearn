from fastapi import APIRouter, Depends, HTTPException

from app.services.auth_service import get_current_admin_user
from app.services.external_api_service import ExternalAPIError, ExternalArticle, fetch_dev_to_articles

# Dev/debug endpoint for the content pipeline, not learner-facing —
# admin-only, same reasoning as content.py.
router = APIRouter(
    prefix="/api/external", tags=["external"], dependencies=[Depends(get_current_admin_user)]
)


@router.get("/test", response_model=list[ExternalArticle])
def test_external_api(tag: str = "programming", limit: int = 5):
    """Development-only endpoint proving FastAPI -> external API -> FastAPI
    works. Not part of the real learning-content pipeline yet — nothing here
    is saved to PostgreSQL (see Phase 6 notes)."""
    try:
        return fetch_dev_to_articles(tag=tag, limit=limit)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
