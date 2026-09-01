from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import GROQ_MODEL
from app.database import get_db
from app.models.ai_draft import AIDraft, DraftStatus
from app.models.question import Question
from app.models.source_article import SourceArticle
from app.models.topic import Topic
from app.schemas.ai import (
    AIDraftResponse,
    AIDraftReviewResponse,
    AITestRequest,
    DraftApprovalRequest,
    GeneratedLearningContent,
)
from app.schemas.question import QuestionResponse
from app.services.ai_service import AIServiceError, generate_learning_content
from app.services.auth_service import get_current_admin_user

# Draft generation/approval/rejection are content-pipeline admin actions,
# not something a normal learner should ever call — same reasoning as
# content.py's router-level gate.
router = APIRouter(prefix="/api/ai", tags=["ai"], dependencies=[Depends(get_current_admin_user)])


def _build_article_content(article: SourceArticle) -> str:
    return f"Title: {article.title}\nDescription: {article.description or ''}\nTags: {article.tags or ''}"


@router.post("/test", response_model=GeneratedLearningContent)
def test_ai(payload: AITestRequest):
    """Development-only endpoint proving FastAPI -> Groq -> structured
    response works. Nothing here is saved to PostgreSQL (see Phase 8 notes)."""
    try:
        return generate_learning_content(payload.topic)
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("/test/article/{article_id}", response_model=GeneratedLearningContent)
def test_ai_from_article(article_id: int, db: Session = Depends(get_db)):
    """Same as /test, but the input comes from a stored SourceArticle. Still
    saves nothing — see /drafts/article/{id} for the version that does."""
    article = db.get(SourceArticle, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Source article not found")

    try:
        return generate_learning_content(_build_article_content(article))
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("/drafts/article/{article_id}", response_model=AIDraftResponse, status_code=201)
def generate_draft(article_id: int, db: Session = Depends(get_db)):
    """Generate an AI draft from a SourceArticle and store it with status
    'generated'. Does NOT create a Question — see Phase 9 notes."""
    article = db.get(SourceArticle, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Source article not found")

    existing_pending = (
        db.query(AIDraft)
        .filter(AIDraft.source_article_id == article_id, AIDraft.status == DraftStatus.GENERATED)
        .first()
    )
    if existing_pending is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"An unreviewed draft (id={existing_pending.id}) already exists for this "
                "article — review (approve/reject) it before generating another."
            ),
        )

    try:
        generated = generate_learning_content(_build_article_content(article))
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    draft = AIDraft(
        source_article_id=article.id,
        question_text=generated.question,
        answer=generated.answer,
        simple_explanation=generated.simple_explanation,
        real_world_example=generated.real_world_example,
        business_relevance=generated.business_relevance,
        difficulty=generated.difficulty,
        keywords=generated.keywords,
        model_name=GROQ_MODEL,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def _build_review_response(draft: AIDraft) -> AIDraftReviewResponse:
    """Enriches a draft with its source article's title/topic/relevance —
    Part 7 (Phase 13): enough to review a draft without a second API call."""
    article = draft.source_article
    return AIDraftReviewResponse(
        **AIDraftResponse.model_validate(draft).model_dump(),
        source_article_title=article.title,
        source_article_topic_name=article.classified_topic.name if article.classified_topic else None,
        source_article_relevance_score=article.relevance_score,
    )


@router.get("/drafts", response_model=list[AIDraftReviewResponse])
def list_drafts(
    status: DraftStatus | None = None,
    source_article_id: int | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Review queue for pending (or any-status) AI drafts — filter by
    ?status=generated to see only what's awaiting a decision."""
    query = db.query(AIDraft)
    if status is not None:
        query = query.filter(AIDraft.status == status)
    if source_article_id is not None:
        query = query.filter(AIDraft.source_article_id == source_article_id)
    drafts = query.order_by(AIDraft.id).offset(offset).limit(limit).all()
    return [_build_review_response(draft) for draft in drafts]


@router.get("/drafts/{draft_id}", response_model=AIDraftReviewResponse)
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.get(AIDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="AI draft not found")
    return _build_review_response(draft)


@router.post("/drafts/{draft_id}/approve", response_model=QuestionResponse)
def approve_draft(draft_id: int, payload: DraftApprovalRequest, db: Session = Depends(get_db)):
    """Create a real Question from an AI draft. This is the ONLY place a
    Question is ever created from AI output — never automatically."""
    draft = db.get(AIDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="AI draft not found")

    if draft.status != DraftStatus.GENERATED:
        raise HTTPException(
            status_code=409,
            detail=f"Draft is already '{draft.status.value}' — cannot approve it again.",
        )

    topic = db.get(Topic, payload.topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    question = Question(
        topic_id=topic.id,
        question_text=draft.question_text,
        answer=draft.answer,
        simple_explanation=draft.simple_explanation,
        real_world_example=draft.real_world_example,
        business_relevance=draft.business_relevance,
        difficulty=draft.difficulty,
        keywords=draft.keywords,
        source_draft_id=draft.id,
    )
    draft.status = DraftStatus.APPROVED
    draft.reviewed_at = datetime.now(timezone.utc)

    # Transaction safety: the new Question and the draft's status/reviewed_at
    # change are committed together in one transaction. If anything fails
    # before commit, rollback() undoes both — the draft is never left
    # "approved" without a matching Question, or vice versa.
    try:
        db.add(question)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to approve draft due to a database error")

    db.refresh(question)
    return question


@router.post("/drafts/{draft_id}/reject", response_model=AIDraftResponse)
def reject_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.get(AIDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="AI draft not found")

    if draft.status != DraftStatus.GENERATED:
        raise HTTPException(
            status_code=409,
            detail=f"Draft is already '{draft.status.value}' — cannot reject it again.",
        )

    draft.status = DraftStatus.REJECTED
    draft.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    return draft
