from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.chat_session import ChatSession
    from app.models.learning_progress import LearningProgress


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Legacy from Phase 5 (pre-authentication) — kept, but no longer used
    # for identifying a user. Nullable so newly-registered users don't need
    # one; the existing dev_user row keeps its original value untouched.
    username: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)

    # Phase 14: real authentication.
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    # Simple boolean role — not a full permissions system (see Phase 14
    # notes in docs/architecture.md). True only for the account managing the
    # content pipeline; normal registered users default to False.
    is_admin: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    learning_progress: Mapped[list["LearningProgress"]] = relationship(back_populates="user")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user")
