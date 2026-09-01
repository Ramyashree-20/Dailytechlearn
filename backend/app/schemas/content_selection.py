from pydantic import BaseModel


class CandidateResponse(BaseModel):
    """Development/debugging view of one candidate — why it was (or would
    be) selected. Not a stable public API contract; the scoring internals
    here may change as the selection algorithm evolves."""

    article_id: int
    title: str
    category_name: str | None
    topic_name: str | None
    importance_score: float
    relevance_score: float
    freshness_score: float
    selection_score: float


class BatchGenerationError(BaseModel):
    article_id: int
    reason: str


class BatchGenerationResult(BaseModel):
    requested: int
    selected: int
    generated: int
    # skipped: candidate became ineligible right before generating.
    # failed: Groq/generation itself failed. Split (Phase 13) so both this
    # endpoint and /api/content/replenish report failures the same way.
    skipped: int
    failed: int = 0
    errors: list[BatchGenerationError] = []
