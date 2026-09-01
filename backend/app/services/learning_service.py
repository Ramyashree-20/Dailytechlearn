from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ai_draft import AIDraft, DraftStatus
from app.models.learning_progress import LearningProgress
from app.models.question import Question
from app.models.topic import Topic
from app.services.adaptive_repetition_service import (
    DEFAULT_EASE_FACTOR,
    MASTERED_REVIEW_COUNT_THRESHOLD,
    ReviewResult,
    calculate_next_review,
)

NEW_QUESTIONS_LIMIT = 5
REVISION_QUESTIONS_LIMIT = 5
RECENT_ACTIVITY_LIMIT = 5
# Generous enough to cover every topic this app currently has (25 as of
# Phase 10) — effectively "all topics with progress," not a real page-size
# limit. The Phase 17 Progress page needs the full list; the Dashboard's
# home view simply displays fewer of them client-side.
TOPICS_IN_PROGRESS_LIMIT = 50


def select_new_questions(
    db: Session, user_id: int, topic_id: int | None = None, limit: int = NEW_QUESTIONS_LIMIT
) -> list[Question]:
    """Questions the user has never learned before, from an active topic
    (Phase 19 — a paused topic's questions shouldn't surface as "new" even
    though the questions themselves still exist; content_selection_service's
    is_eligible() already applies this same rule on the ingestion side).

    Ordered by topic importance (Phase 10/11) first, then question id as a
    stable, deterministic tie-breaker. Content relevance isn't included here
    yet — that's a property of the SourceArticle a Question came from
    (Phase 11), and manually-created questions (e.g. the Phase 4 seed data)
    don't have one; see Phase 11 notes for where this may extend later.
    """
    learned_question_ids = db.query(LearningProgress.question_id).filter(
        LearningProgress.user_id == user_id
    )

    query = (
        db.query(Question)
        .join(Topic, Question.topic_id == Topic.id)
        .filter(~Question.id.in_(learned_question_ids), Topic.active.is_(True))
    )
    if topic_id is not None:
        query = query.filter(Question.topic_id == topic_id)

    return query.order_by(Topic.importance.desc(), Question.id.asc()).limit(limit).all()


def select_revision_questions(
    db: Session, user_id: int, topic_id: int | None = None, limit: int = REVISION_QUESTIONS_LIMIT
) -> list[Question]:
    """Questions the user has previously learned AND are due for revision
    (Phase 12: next_review_at <= now) — a question that isn't due yet is
    NOT a revision candidate. Most-overdue first (oldest next_review_at),
    question id as a stable, deterministic tie-breaker."""
    now = datetime.now(timezone.utc)
    query = (
        db.query(Question)
        .join(LearningProgress, LearningProgress.question_id == Question.id)
        .filter(LearningProgress.user_id == user_id, LearningProgress.next_review_at <= now)
    )
    if topic_id is not None:
        query = query.filter(Question.topic_id == topic_id)

    return query.order_by(LearningProgress.next_review_at.asc(), Question.id.asc()).limit(limit).all()


def mark_question_learned(
    db: Session, user_id: int, question_id: int, result: ReviewResult = "easy"
) -> LearningProgress:
    """Create or update the (user, question) progress record, computing the
    next adaptive-repetition due date (Phase 18). Never creates a
    duplicate — the unique constraint on (user_id, question_id) guarantees
    there is at most one row to find or update."""
    progress = (
        db.query(LearningProgress)
        .filter(LearningProgress.user_id == user_id, LearningProgress.question_id == question_id)
        .first()
    )

    if progress is None:
        # A brand-new row has no prior reviews yet -> review_count 0 and
        # the default ease factor, same starting point every question gets.
        current_review_count = 0
        current_ease_factor = DEFAULT_EASE_FACTOR
        previous_interval_days = 0
    else:
        current_review_count = progress.review_count
        current_ease_factor = progress.ease_factor
        # The interval that was scheduled at the LAST review — derived from
        # the row's current (pre-update) timestamps rather than stored
        # separately: next_review_at was set, last time, to exactly
        # last_reviewed_at + that interval.
        previous_interval_days = (progress.next_review_at - progress.last_reviewed_at).days

    new_review_count, new_ease_factor, next_review_at = calculate_next_review(
        current_review_count, current_ease_factor, previous_interval_days, result
    )

    if progress is None:
        progress = LearningProgress(
            user_id=user_id,
            question_id=question_id,
            review_count=new_review_count,
            ease_factor=new_ease_factor,
            next_review_at=next_review_at,
        )
        db.add(progress)
    else:
        progress.last_reviewed_at = datetime.now(timezone.utc)
        progress.review_count = new_review_count
        progress.ease_factor = new_ease_factor
        progress.next_review_at = next_review_at

    db.commit()
    db.refresh(progress)
    return progress


def get_pipeline_status(db: Session, user_id: int) -> dict:
    """Read-only counts for understanding whether the daily learning pool
    is healthy — see Part 8 (Phase 12) / the Phase 11 "honest limitation"
    notes. Never modifies anything."""
    now = datetime.now(timezone.utc)

    approved_question_count = db.query(Question).count()

    learned_question_ids = db.query(LearningProgress.question_id).filter(
        LearningProgress.user_id == user_id
    )
    # Same "active topic" rule as select_new_questions() (Phase 19) — this
    # count should describe what a learner could actually be shown, not
    # include questions from a paused topic they'll never see.
    available_new_questions = (
        db.query(Question)
        .join(Topic, Question.topic_id == Topic.id)
        .filter(~Question.id.in_(learned_question_ids), Topic.active.is_(True))
        .count()
    )

    due_revision_count = (
        db.query(LearningProgress)
        .filter(LearningProgress.user_id == user_id, LearningProgress.next_review_at <= now)
        .count()
    )

    pending_ai_draft_count = db.query(AIDraft).filter(AIDraft.status == DraftStatus.GENERATED).count()

    return {
        "approved_question_count": approved_question_count,
        "available_new_questions": available_new_questions,
        "due_revision_count": due_revision_count,
        "pending_ai_draft_count": pending_ai_draft_count,
    }


def _compute_streak_days(activity_dates: set[date]) -> int:
    """Consecutive-day streak ending today (or yesterday, so a learner who
    simply hasn't studied yet *today* doesn't see their streak drop to zero
    prematurely) — the same forgiving definition apps like Duolingo use.

    Approximation, not exact history: LearningProgress is a current-state
    table (Phase 5 design decision, still true), not an event log — it only
    remembers each question's first-learned date and its MOST RECENT review
    date, not every day it was ever touched. A day where a question was
    reviewed but then reviewed again later on a different day can "disappear"
    from this calculation once the newer date overwrites the old one, unless
    some other question's activity also covers that day. Good enough for a
    motivational streak count; not a precise audit log. See docs/architecture.md.
    """
    if not activity_dates:
        return 0
    today = datetime.now(timezone.utc).date()
    cursor = today if today in activity_dates else today - timedelta(days=1)
    if cursor not in activity_dates:
        return 0
    streak = 0
    while cursor in activity_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def get_dashboard(db: Session, user_id: int) -> dict:
    """Learner dashboard/progress data (Phase 16, extended Phase 17) — a
    read-only aggregation entirely over existing
    LearningProgress/Question/Topic data. No new progress table; this only
    counts/groups what mark_question_learned() already writes."""
    now = datetime.now(timezone.utc)

    learned_count = db.query(LearningProgress).filter(LearningProgress.user_id == user_id).count()
    total_approved_questions = db.query(Question).count()

    learned_question_ids = db.query(LearningProgress.question_id).filter(
        LearningProgress.user_id == user_id
    )
    # Same "active topic" rule as select_new_questions() (Phase 19).
    new_available_count = (
        db.query(Question)
        .join(Topic, Question.topic_id == Topic.id)
        .filter(~Question.id.in_(learned_question_ids), Topic.active.is_(True))
        .count()
    )

    due_revision_count = (
        db.query(LearningProgress)
        .filter(LearningProgress.user_id == user_id, LearningProgress.next_review_at <= now)
        .count()
    )

    progress_percent = (
        round(learned_count / total_approved_questions * 100, 1) if total_approved_questions else 0.0
    )

    # "Mastered" = enough consecutive successful reviews (without an
    # intervening "hard" reset) to be well-consolidated in memory — the
    # same MASTERED_REVIEW_COUNT_THRESHOLD adaptive_repetition_service.py
    # documents, reused here rather than re-defining "mastered" against a
    # second, independent threshold.
    mastered_count = (
        db.query(LearningProgress)
        .filter(
            LearningProgress.user_id == user_id,
            LearningProgress.review_count >= MASTERED_REVIEW_COUNT_THRESHOLD,
        )
        .count()
    )

    total_reviews_completed = (
        db.query(func.coalesce(func.sum(LearningProgress.review_count), 0))
        .filter(LearningProgress.user_id == user_id)
        .scalar()
    )

    difficulty_rows = (
        db.query(Question.difficulty, func.count(LearningProgress.id))
        .join(LearningProgress, LearningProgress.question_id == Question.id)
        .filter(LearningProgress.user_id == user_id)
        .group_by(Question.difficulty)
        .all()
    )
    difficulty_breakdown = {difficulty.value: count for difficulty, count in difficulty_rows}

    activity_dates: set[date] = set()
    for first_learned_at, last_reviewed_at in db.query(
        LearningProgress.first_learned_at, LearningProgress.last_reviewed_at
    ).filter(LearningProgress.user_id == user_id):
        activity_dates.add(first_learned_at.date())
        activity_dates.add(last_reviewed_at.date())
    current_streak_days = _compute_streak_days(activity_dates)

    recent_rows = (
        db.query(LearningProgress)
        .join(Question, LearningProgress.question_id == Question.id)
        .filter(LearningProgress.user_id == user_id)
        .order_by(LearningProgress.last_reviewed_at.desc())
        .limit(RECENT_ACTIVITY_LIMIT)
        .all()
    )
    recent_activity = [
        {
            "question_id": row.question_id,
            "question_text": row.question.question_text,
            "last_reviewed_at": row.last_reviewed_at,
            "review_count": row.review_count,
        }
        for row in recent_rows
    ]

    topic_totals = dict(
        db.query(Topic.id, func.count(Question.id)).join(Question, Question.topic_id == Topic.id).group_by(Topic.id)
    )
    topic_rows = (
        db.query(Topic.id, Topic.name, func.count(LearningProgress.id))
        .join(Question, Question.topic_id == Topic.id)
        .join(LearningProgress, LearningProgress.question_id == Question.id)
        .filter(LearningProgress.user_id == user_id)
        .group_by(Topic.id, Topic.name)
        .order_by(func.count(LearningProgress.id).desc())
        .limit(TOPICS_IN_PROGRESS_LIMIT)
        .all()
    )
    topics_in_progress = [
        {
            "topic_id": topic_id,
            "topic_name": name,
            "learned_count": count,
            "total_questions": topic_totals.get(topic_id, 0),
        }
        for topic_id, name, count in topic_rows
    ]

    return {
        "learned_count": learned_count,
        "due_revision_count": due_revision_count,
        "new_available_count": new_available_count,
        "total_approved_questions": total_approved_questions,
        "progress_percent": progress_percent,
        "mastered_count": mastered_count,
        "total_reviews_completed": total_reviews_completed,
        "current_streak_days": current_streak_days,
        "difficulty_breakdown": difficulty_breakdown,
        "recent_activity": recent_activity,
        "topics_in_progress": topics_in_progress,
    }
