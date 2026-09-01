from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.category import Category
from app.models.source_article import SourceArticle
from app.models.topic import Topic
from app.schemas.content_classification import ClassificationResult
from app.schemas.content_pipeline import ContentPipelineStatusResponse, ReplenishResult
from app.schemas.content_selection import CandidateResponse
from app.schemas.source_article import IngestionResult, SourceArticleResponse
from app.services.ai_service import AIServiceError
from app.services.auth_service import get_current_admin_user
from app.services.classification_service import classify_article
from app.services.content_ingestion_service import ingest_dev_to_articles
from app.services.content_pipeline_service import (
    MAX_BATCH_SIZE,
    get_content_pipeline_status,
    replenish_content,
)
from app.services.content_selection_service import get_candidates
from app.services.external_api_service import ExternalAPIError

# Every endpoint here manages the content pipeline (ingestion,
# classification, replenishment) — admin-only, not something a normal
# learner should ever call. Gated at the router level since ALL of this
# router's endpoints are admin-facing (see Phase 14 notes).
router = APIRouter(
    prefix="/api/content", tags=["content"], dependencies=[Depends(get_current_admin_user)]
)


@router.post("/ingest", response_model=IngestionResult)
def ingest_content(tag: str = "programming", limit: int = 5, db: Session = Depends(get_db)):
    """Development endpoint: fetch articles from Dev.to and store any that
    aren't already saved. Safe to call repeatedly — see Phase 7 notes."""
    try:
        return ingest_dev_to_articles(db, tag=tag, limit=limit)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/articles", response_model=list[SourceArticleResponse])
def list_articles(
    source: str | None = None,
    tag: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(SourceArticle)
    if source is not None:
        query = query.filter(SourceArticle.source_name == source)
    if tag is not None:
        query = query.filter(SourceArticle.tags.ilike(f"%{tag}%"))
    return query.order_by(SourceArticle.id).offset(offset).limit(limit).all()


@router.get("/articles/{article_id}", response_model=SourceArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.get(SourceArticle, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Source article not found")
    return article


@router.post("/classify/{article_id}", response_model=ClassificationResult)
def classify_article_endpoint(article_id: int, db: Session = Depends(get_db)):
    """Ask Groq which of our existing Category/Topic this article best fits.

    Phase 10: read-only. Phase 11: when the AI's category AND topic both
    match a real row, the classification is persisted onto the article
    (so candidate selection doesn't need to re-call Groq for the same
    article every time). A hallucinated (non-matching) name is NEVER
    persisted — Category/Topic/SourceArticle rows are only ever written
    here when the match is real."""
    article = db.get(SourceArticle, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Source article not found")

    try:
        classification = classify_article(
            db, article.title, article.description or "", article.tags or ""
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    matched_category = db.query(Category).filter(Category.name == classification.category).first()
    matched_topic = db.query(Topic).filter(Topic.name == classification.topic).first()

    if matched_category is not None and matched_topic is not None:
        article.classified_category_id = matched_category.id
        article.classified_topic_id = matched_topic.id
        article.classified_difficulty = classification.difficulty
        article.relevance_score = classification.relevance_score
        article.classified_at = datetime.now(timezone.utc)
        db.commit()

    return ClassificationResult(
        classification=classification,
        matched_category_id=matched_category.id if matched_category else None,
        matched_topic_id=matched_topic.id if matched_topic else None,
    )


@router.get("/candidates", response_model=list[CandidateResponse])
def list_candidates(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    """Development/debugging endpoint: which classified articles are
    currently eligible new-content candidates, and why (their scoring
    breakdown). Not a stable public API — internals may change."""
    candidates = get_candidates(db, limit=limit)
    return [
        CandidateResponse(
            article_id=c.article.id,
            title=c.article.title,
            category_name=c.topic.category.name if c.topic.category else None,
            topic_name=c.topic.name,
            importance_score=c.importance_score,
            relevance_score=c.relevance_score,
            freshness_score=c.freshness_score,
            selection_score=c.selection_score,
        )
        for c in candidates
    ]


@router.get("/pipeline-status", response_model=ContentPipelineStatusResponse)
def get_content_pipeline_status_endpoint(user_id: int | None = None, db: Session = Depends(get_db)):
    """Read-only admin view of the whole content pipeline's health — see
    Phase 13 notes. Pass ?user_id= to also include that user's
    available-new/due-revision counts; omit it for a purely global view.
    Never modifies anything."""
    return get_content_pipeline_status(db, user_id=user_id)


@router.post("/replenish", response_model=ReplenishResult)
def replenish_content_endpoint(
    count: int | None = Query(default=None, ge=1, le=MAX_BATCH_SIZE),
    db: Session = Depends(get_db),
):
    """Development/admin endpoint: generate enough AIDrafts to work toward
    the target content pool size (or up to `count`, if given) — never more
    than MAX_BATCH_SIZE drafts in one call, regardless of what's requested.
    Creates ONLY AIDrafts — never approves anything or creates a Question;
    see Phase 9's approval boundary, unchanged."""
    return replenish_content(db, requested_count=count)
