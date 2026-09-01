from pydantic import BaseModel, ConfigDict, Field

from app.models.question import DifficultyLevel


class ContentClassification(BaseModel):
    """An AI-suggested classification of a SourceArticle. A RECOMMENDATION,
    not a database write — see Phase 10 notes in docs/architecture.md.
    category/topic are free text the model was asked to copy from our
    existing taxonomy; nothing guarantees they actually match a real row
    (see ClassificationResult, which checks that separately)."""

    category: str
    topic: str
    difficulty: DifficultyLevel
    relevance_score: int = Field(ge=1, le=5)
    reasoning: str


class ClassificationResult(BaseModel):
    """What the API actually returns: the raw AI suggestion, plus whether it
    matched something real in our curated taxonomy. matched_*_id is None
    when the AI named a category/topic that doesn't exist — a safe,
    explicit signal instead of silently trusting free text."""

    model_config = ConfigDict(from_attributes=True)

    classification: ContentClassification
    matched_category_id: int | None
    matched_topic_id: int | None
