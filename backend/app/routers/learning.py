from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.learning_progress import LearningProgress
from app.models.question import Question
from app.models.user import User
from app.schemas.content_selection import BatchGenerationResult
from app.schemas.learning import (
    DailyLearningResponse,
    DashboardResponse,
    LearningCompleteRequest,
    LearningProgressResponse,
    PipelineStatusResponse,
)
from app.schemas.learning_assistant import AssistantRequest, AssistantResponse
from app.services.ai_service import AIServiceError
from app.services.auth_service import get_current_admin_user, get_current_user
from app.services.content_pipeline_service import generate_drafts_for_candidates
from app.services.content_selection_service import get_candidates
from app.services.learning_assistant_service import ask_assistant
from app.services.learning_service import (
    get_dashboard,
    get_pipeline_status,
    mark_question_learned,
    select_new_questions,
    select_revision_questions,
)

router = APIRouter(prefix="/api/learning", tags=["learning"])


@router.post("/complete", response_model=LearningProgressResponse)
def complete_question(
    payload: LearningCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    return mark_question_learned(db, current_user.id, payload.question_id, result=payload.result)


@router.get("/progress", response_model=list[LearningProgressResponse])
def get_user_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(LearningProgress)
        .filter(LearningProgress.user_id == current_user.id)
        .order_by(LearningProgress.first_learned_at)
        .all()
    )


@router.post("/generate-drafts", response_model=BatchGenerationResult, dependencies=[Depends(get_current_admin_user)])
def generate_drafts_batch(limit: int = Query(default=5, ge=1, le=20), db: Session = Depends(get_db)):
    """Development endpoint: rank the top `limit` current candidates and
    generate an AIDraft for each, regardless of whether the content pool
    actually needs that many. Creates ONLY AIDrafts (status=generated) —
    never a Question; see Phase 9's approval boundary. Resilient — see
    generate_drafts_for_candidates(). For pool-size-aware generation, prefer
    POST /api/content/replenish (Phase 13), which calculates how many are
    actually needed and shares this same generation loop."""
    candidates = get_candidates(db, limit=limit)
    result = generate_drafts_for_candidates(db, candidates)

    return BatchGenerationResult(
        requested=limit,
        selected=len(candidates),
        generated=result["generated"],
        skipped=result["skipped"],
        failed=result["failed"],
        errors=result["errors"],
    )


@router.get("/today", response_model=DailyLearningResponse)
def get_today_learning(
    topic_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_questions = select_new_questions(db, current_user.id, topic_id=topic_id)
    revision_questions = select_revision_questions(db, current_user.id, topic_id=topic_id)
    return {"new_questions": new_questions, "revision_questions": revision_questions}


@router.get("/pipeline-status", response_model=PipelineStatusResponse)
def get_pipeline_status_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Read-only visibility into the daily learning pool's health for this
    user (Part 8): total approved questions, how many are new for them, how
    many are due for revision, and how many AI drafts are awaiting review.
    Never modifies the database."""
    return get_pipeline_status(db, current_user.id)


@router.get("/dashboard", response_model=DashboardResponse)
def get_learning_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Phase 16 learner dashboard: counts, progress percentage, recent
    activity, and topics-in-progress — all derived from the existing
    LearningProgress table (see learning_service.get_dashboard()). No new
    progress table; purely a read-only aggregation."""
    return get_dashboard(db, current_user.id)


@router.post("/assistant", response_model=AssistantResponse, dependencies=[Depends(get_current_user)])
def ask_learning_assistant(payload: AssistantRequest, db: Session = Depends(get_db)):
    """Ask the AI Learning Assistant a question — either general, or about
    a specific Question the learner is currently viewing (`question_id`).
    Stateless: nothing here is saved to PostgreSQL, and no Question is ever
    created/modified/approved/rejected by this endpoint (see Phase 9's
    approval boundary, untouched). `question_id` is always loaded from our
    own database, never trusted from arbitrary client-supplied content."""
    question = None
    if payload.question_id is not None:
        question = db.get(Question, payload.question_id)
        if question is None:
            raise HTTPException(status_code=404, detail="Question not found")

    try:
        return ask_assistant(payload.message, question, payload.history)
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
