from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.question import QuestionResponse
from app.services.adaptive_repetition_service import ReviewResult


class LearningCompleteRequest(BaseModel):
    # No user_id here — Phase 14 derives the user from the authenticated
    # JWT (see get_current_user), never from a client-supplied field.
    question_id: int
    # Optional so existing callers (e.g. the Phase 5 frontend "Learned"
    # button) keep working unchanged. "easy" = grows the interval (rate
    # depends on this question's ease factor); "hard" = resets the review
    # streak and shortens the interval (see adaptive_repetition_service.py,
    # Phase 18).
    result: ReviewResult = "easy"


class LearningProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: int
    first_learned_at: datetime
    last_reviewed_at: datetime
    review_count: int
    next_review_at: datetime


class DailyLearningResponse(BaseModel):
    new_questions: list[QuestionResponse]
    revision_questions: list[QuestionResponse]


class PipelineStatusResponse(BaseModel):
    """Read-only visibility into whether the daily learning pool is
    healthy for this user — see Phase 11/12 notes on why AI drafts can
    outpace human review. Not used to change any selection behavior."""

    approved_question_count: int
    available_new_questions: int
    due_revision_count: int
    pending_ai_draft_count: int


class RecentActivityItem(BaseModel):
    question_id: int
    question_text: str
    last_reviewed_at: datetime
    review_count: int


class TopicProgressSummary(BaseModel):
    topic_id: int
    topic_name: str
    learned_count: int
    total_questions: int


class DashboardResponse(BaseModel):
    """Learner dashboard/progress data (Phase 16, extended Phase 17) —
    entirely derived from the existing LearningProgress/Question/Topic
    tables (see learning_service.py's get_dashboard()). No new
    progress-tracking table was introduced; this is a read-only
    aggregation view over data that already exists. Powers both the
    Phase 17 /dashboard home page and the /dashboard/progress page — one
    endpoint, no duplicate data source."""

    learned_count: int
    due_revision_count: int
    new_available_count: int
    total_approved_questions: int
    progress_percent: float
    mastered_count: int
    total_reviews_completed: int
    # Approximate — see _compute_streak_days() in learning_service.py for
    # why LearningProgress being a current-state table (not an event log)
    # makes this a best-effort count, not an exact historical record.
    current_streak_days: int
    difficulty_breakdown: dict[str, int]
    recent_activity: list[RecentActivityItem]
    topics_in_progress: list[TopicProgressSummary]
