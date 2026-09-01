"""Decides HOW MUCH new content the pipeline needs, and orchestrates
generating drafts for that many eligible candidates. This file owns exactly
one responsibility — "how much, and which N candidates" — and deliberately
reuses (never duplicates) the other two:

- content_selection_service.py:  WHICH articles are eligible, and ranking.
- draft_generation_service.py:   HOW ONE article becomes an AIDraft.

See Phase 13 notes in docs/architecture.md.
"""

from sqlalchemy.orm import Session

from app.models.ai_draft import AIDraft, DraftStatus
from app.models.question import Question
from app.models.source_article import SourceArticle
from app.services.ai_service import AIServiceError
from app.services.content_selection_service import (
    Candidate,
    count_eligible_candidates,
    get_candidates,
)
from app.services.draft_generation_service import DraftGenerationError, generate_learning_draft

# The "content pool" target: roughly a week's worth of new questions at the
# intended 5/day rate. One named, adjustable constant — never hardcode this
# number elsewhere. Purely a product decision, not a technical requirement.
TARGET_NEW_POOL_SIZE = 35

# Hard ceiling on how many Groq generation calls ONE replenish request can
# ever trigger — enforced here in backend code (not just documented, and
# not only validated by the API layer), so no request can ever trigger
# thousands of Groq calls regardless of what a caller asks for.
MAX_BATCH_SIZE = 10


def get_content_pipeline_status(db: Session, user_id: int | None = None) -> dict:
    """Read-only pipeline health. Global counts always included;
    available_new_questions/due_revision_count only when user_id is given,
    since "new"/"due" are inherently per-user concepts. Never modifies
    anything."""
    total_source_articles = db.query(SourceArticle).count()
    classified_articles = (
        db.query(SourceArticle).filter(SourceArticle.classified_topic_id.isnot(None)).count()
    )
    eligible_candidates = count_eligible_candidates(db)
    pending_drafts = db.query(AIDraft).filter(AIDraft.status == DraftStatus.GENERATED).count()
    approved_questions = db.query(Question).count()
    rejected_drafts = db.query(AIDraft).filter(AIDraft.status == DraftStatus.REJECTED).count()

    recommended_generation_count = max(0, TARGET_NEW_POOL_SIZE - approved_questions)
    pool_status = "healthy" if approved_questions >= TARGET_NEW_POOL_SIZE else "needs_content"

    status = {
        "total_source_articles": total_source_articles,
        "classified_articles": classified_articles,
        "eligible_candidates": eligible_candidates,
        "pending_drafts": pending_drafts,
        "approved_questions": approved_questions,
        "rejected_drafts": rejected_drafts,
        "target_new_pool_size": TARGET_NEW_POOL_SIZE,
        "pool_status": pool_status,
        "recommended_generation_count": recommended_generation_count,
    }

    if user_id is not None:
        # Local import: avoids a circular import (learning_service doesn't
        # need to know about this module).
        from app.services.learning_service import get_pipeline_status as get_user_status

        user_status = get_user_status(db, user_id)
        status["available_new_questions"] = user_status["available_new_questions"]
        status["due_revision_count"] = user_status["due_revision_count"]

    return status


def generate_drafts_for_candidates(db: Session, candidates: list[Candidate]) -> dict:
    """Shared resilient batch-generation loop — tries each candidate,
    isolating failures so one bad article never corrupts the rest. Used by
    both /api/learning/generate-drafts (Phase 11) and /api/content/replenish
    (Phase 13), so this logic lives in exactly one place.

    Distinguishes WHY a candidate didn't produce a draft: "skipped" means it
    turned out ineligible right before generating (e.g. a duplicate check
    fired); "failed" means Groq/generation itself broke (network, bad
    model, invalid output).
    """
    generated = 0
    skipped = 0
    failed = 0
    errors: list[dict] = []

    for candidate in candidates:
        try:
            generate_learning_draft(db, candidate.article)
            generated += 1
        except DraftGenerationError as exc:
            db.rollback()
            skipped += 1
            errors.append({"article_id": candidate.article.id, "reason": str(exc)})
        except AIServiceError as exc:
            db.rollback()
            failed += 1
            errors.append({"article_id": candidate.article.id, "reason": str(exc)})

    return {"generated": generated, "skipped": skipped, "failed": failed, "errors": errors}


def replenish_content(db: Session, requested_count: int | None = None) -> dict:
    """Calculates how many drafts are needed (or uses requested_count, if
    given), clamps to MAX_BATCH_SIZE, and generates that many from the
    best-ranked eligible candidates. NEVER creates a Question or approves
    anything — see Phase 9's approval boundary, completely untouched here."""
    approved_questions = db.query(Question).count()
    calculated_need = max(0, TARGET_NEW_POOL_SIZE - approved_questions)

    target = requested_count if requested_count is not None else calculated_need
    target = max(0, min(target, MAX_BATCH_SIZE))

    candidates = get_candidates(db, limit=target) if target > 0 else []
    result = generate_drafts_for_candidates(db, candidates)

    return {
        "requested": target,
        "max_batch_size": MAX_BATCH_SIZE,
        "candidates_considered": len(candidates),
        **result,
    }
