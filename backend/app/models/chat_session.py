from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage
    from app.models.question import Question
    from app.models.user import User


class ChatSession(Base):
    """One AI Learning Assistant conversation (Phase 16) — the persistent
    upgrade to Phase 15's stateless POST /api/learning/assistant. Belongs to
    exactly one user; optionally anchors to the Question the learner was
    viewing when they started it.

    Deliberately does NOT copy the Question's content onto the session —
    only its id. The question's text/answer/etc. can change meaning only
    once (it's immutable after creation in this app), but more importantly,
    duplicating it per-session would mean re-fetching the same context data
    over and over across many sessions for no benefit; a live FK lookup
    keeps there being exactly one source of truth. See docs/architecture.md.
    """

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    question_id: Mapped[int | None] = mapped_column(ForeignKey("questions.id"), nullable=True)

    # Deterministic, derived from the first user message (or the linked
    # question, until a first message exists) — never a second Groq call.
    # See _derive_title() in chat_service.py.
    title: Mapped[str] = mapped_column(String(120), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Bumped whenever a message is added, so the session list can sort by
    # "most recently active" rather than "most recently created".
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    question: Mapped["Question | None"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.id"
    )
