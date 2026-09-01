from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ai_draft import DraftStatus
from app.models.question import DifficultyLevel


class AITestRequest(BaseModel):
    topic: str = Field(min_length=1)


class GeneratedLearningContent(BaseModel):
    """AI-generated draft learning content. NOT a Question — see Phase 8/9
    notes in docs/architecture.md. This is unreviewed model output, kept
    structurally valid by this schema but not vetted for accuracy.

    difficulty/keywords were added in Phase 9: Question.difficulty is
    required (non-null), and inventing a default value would be silently
    fabricating data. Difficulty and keywords are judgments about the
    content itself, which the model can reasonably make — unlike topic_id,
    which requires knowing our specific curated Topic taxonomy and stays a
    human decision made at approval time (see Phase 9 notes).
    """

    question: str
    answer: str
    simple_explanation: str
    real_world_example: str
    business_relevance: str
    difficulty: DifficultyLevel
    keywords: str | None = None


class AIDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_article_id: int
    question_text: str
    answer: str
    simple_explanation: str
    real_world_example: str
    business_relevance: str
    difficulty: DifficultyLevel
    keywords: str | None
    model_name: str
    status: DraftStatus
    created_at: datetime
    reviewed_at: datetime | None


class DraftApprovalRequest(BaseModel):
    topic_id: int


class AIDraftReviewResponse(AIDraftResponse):
    """AIDraftResponse plus enough of the source article's context (title,
    classified topic, relevance) to review a draft without a second API
    call — for a future admin review screen (Phase 13, Part 7)."""

    source_article_title: str
    source_article_topic_name: str | None
    source_article_relevance_score: int | None
