from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.question import DifficultyLevel

if TYPE_CHECKING:
    from app.models.ai_draft import AIDraft
    from app.models.category import Category
    from app.models.topic import Topic


class SourceArticle(Base):
    """Raw external content pulled in by the content ingestion pipeline.

    This is NOT learning content — see Phase 7 notes in
    docs/architecture.md. A SourceArticle only ever becomes a Question
    through a deliberate future transformation step.

    classified_*/relevance_score/classified_at (Phase 11): the persisted
    result of the most recent successful classification (see
    app/routers/content.py's classify endpoint). NULL until classified —
    candidate selection treats an unclassified article as ineligible.
    """

    __tablename__ = "source_articles"
    __table_args__ = (
        UniqueConstraint("source_name", "external_id", name="uq_source_articles_source_external_id"),
        CheckConstraint("relevance_score BETWEEN 1 AND 5", name="ck_source_articles_relevance_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    # Comma-separated, raw from the source — not yet mapped to our Topic table.
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    classified_category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    classified_topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    classified_difficulty: Mapped[DifficultyLevel | None] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"), nullable=True
    )
    relevance_score: Mapped[int | None] = mapped_column(nullable=True)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ai_drafts: Mapped[list["AIDraft"]] = relationship(back_populates="source_article")
    classified_category: Mapped["Category | None"] = relationship()
    classified_topic: Mapped["Topic | None"] = relationship()
