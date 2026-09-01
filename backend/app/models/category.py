from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.topic import Topic


class Category(Base):
    """A curated top-level grouping of Topics (e.g. "AI & Machine Learning").

    A small, deliberately-designed taxonomy — see Phase 10 notes in
    docs/architecture.md. Never auto-created from external tags/AI output.
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    topics: Mapped[list["Topic"]] = relationship(back_populates="category")
