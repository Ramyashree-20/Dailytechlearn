import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ai_draft import AIDraft
    from app.models.chat_session import ChatSession
    from app.models.learning_progress import LearningProgress
    from app.models.topic import Topic


class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("source_draft_id", name="uq_questions_source_draft_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), nullable=False)
    # Traceability to the AI draft this Question was approved from, if any.
    # NULL for manually-created questions (e.g. the Phase 4 seed data).
    source_draft_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_drafts.id"), nullable=True
    )

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    simple_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    real_world_example: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_relevance: Mapped[str | None] = mapped_column(Text, nullable=True)

    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"), nullable=False
    )
    # Comma-separated for now, e.g. "docker, container, deployment" — see Phase 3 notes.
    keywords: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    topic: Mapped["Topic"] = relationship(back_populates="questions")
    learning_progress: Mapped[list["LearningProgress"]] = relationship(back_populates="question")
    source_draft: Mapped["AIDraft | None"] = relationship()
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="question")
