from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """The public/safe view of a User — NEVER includes password_hash.
    Used by both /api/auth/register and /api/auth/me (Phase 14)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str | None
    is_admin: bool
    created_at: datetime
