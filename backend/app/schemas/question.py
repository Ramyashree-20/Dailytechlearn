from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.question import DifficultyLevel


class QuestionBase(BaseModel):
    topic_id: int
    question_text: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    simple_explanation: str | None = None
    real_world_example: str | None = None
    business_relevance: str | None = None
    difficulty: DifficultyLevel
    keywords: str | None = None


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(QuestionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
