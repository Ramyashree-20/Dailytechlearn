from typing import Literal

from pydantic import BaseModel

from app.schemas.content_selection import BatchGenerationError


class ContentPipelineStatusResponse(BaseModel):
    """Read-only admin view of the whole content pipeline's health — see
    Phase 13 notes in docs/architecture.md. available_new_questions and
    due_revision_count are only populated when a user_id is supplied
    (revision/new-ness are inherently per-user concepts); everything else
    is global."""

    total_source_articles: int
    classified_articles: int
    eligible_candidates: int
    pending_drafts: int
    approved_questions: int
    rejected_drafts: int
    target_new_pool_size: int
    pool_status: Literal["healthy", "needs_content"]
    recommended_generation_count: int
    available_new_questions: int | None = None
    due_revision_count: int | None = None


class ReplenishResult(BaseModel):
    """requested is the number of drafts ACTUALLY attempted this call —
    already clamped to MAX_BATCH_SIZE and to how many eligible candidates
    exist, so it may be lower than a caller-supplied count."""

    requested: int
    max_batch_size: int
    candidates_considered: int
    generated: int
    skipped: int
    failed: int
    errors: list[BatchGenerationError] = []
