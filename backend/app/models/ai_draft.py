import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.question import DifficultyLevel

if TYPE_CHECKING:
    from app.models.source_article import SourceArticle


class DraftStatus(str, enum.Enum):
    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"


class AIDraft(Base):
    """One AI-generated attempt at turning a SourceArticle into learning
    content. NOT a Question — see Phase 9 notes in docs/architecture.md.

    Allowed status transitions: generated -> approved, generated -> rejected.
    Both are terminal; approved/rejected drafts are never modified again.
    """

    __tablename__ = "ai_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_article_id: Mapped[int] = mapped_column(ForeignKey("source_articles.id"), nullable=False)

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    simple_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    real_world_example: Mapped[str] = mapped_column(Text, nullable=False)
    business_relevance: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"), nullable=False
    )
    keywords: Mapped[str | None] = mapped_column(String(255), nullable=True)

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[DraftStatus] = mapped_column(
        Enum(DraftStatus, name="draft_status"), default=DraftStatus.GENERATED, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source_article: Mapped["SourceArticle"] = relationship(back_populates="ai_drafts")
