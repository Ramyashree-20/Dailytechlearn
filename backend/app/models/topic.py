from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.question import Question


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        CheckConstraint("importance BETWEEN 1 AND 5", name="ck_topics_importance_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)

    # Nullable: existing topics are backfilled by the seed script (Phase 10),
    # not by the migration — a topic without a category is a transient state,
    # not a design goal.
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    # How useful this topic is for an AI/software engineer in general — NOT
    # the learner's personal skill level. 1=low, 2=normal, 3=important,
    # 4=very important, 5=critical. Defaults to 3 so existing topics (all
    # genuinely useful) get a sensible value without manual backfill.
    importance: Mapped[int] = mapped_column(Integer, server_default="3", nullable=False)
    # Soft on/off switch for future selection — pausing a topic without
    # deleting it (which would orphan its questions and learning history).
    active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    category: Mapped["Category | None"] = relationship(back_populates="topics")
    questions: Mapped[list["Question"]] = relationship(back_populates="topic")
