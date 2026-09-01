from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.question import Question
    from app.models.user import User


class LearningProgress(Base):
    __tablename__ = "learning_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_learning_progress_user_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)

    first_learned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    review_count: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    # Phase 12: when this question becomes due for revision again. Computed
    # by app/services/adaptive_repetition_service.py (Phase 18 — replaced
    # the original fixed lookup table) from review_count/ease_factor — see
    # docs/architecture.md for the algorithm. server_default=now() is a
    # defensive fallback only (this table was empty when the column was
    # added, so no real backfill was needed) — every row written through the
    # app always sets this explicitly.
    next_review_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Phase 18: how easily THIS learner remembers THIS specific question —
    # starts at adaptive_repetition_service.DEFAULT_EASE_FACTOR and drifts
    # up on "easy" reviews, down on "hard" ones (floored at MIN_EASE_FACTOR).
    # Existing rows were backfilled to the same default via the migration's
    # server_default — nobody's history was treated as "already known" to
    # be easier or harder than average.
    ease_factor: Mapped[float] = mapped_column(Float, server_default="2.5", nullable=False)

    user: Mapped["User"] = relationship(back_populates="learning_progress")
    question: Mapped["Question"] = relationship(back_populates="learning_progress")
