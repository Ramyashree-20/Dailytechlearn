"""Request/response shapes for persistent AI chat (Phase 16) — the
ChatSession/ChatMessage-backed upgrade to Phase 15's stateless
POST /api/learning/assistant (which still exists unchanged)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.chat_message import ChatRole

MAX_MESSAGE_LENGTH = 2000


class CreateChatSessionRequest(BaseModel):
    # The Question the learner was viewing when they opened the assistant,
    # if any. The backend loads the real row itself — see routers/chat.py —
    # never trusting question content from the client.
    question_id: int | None = None


class SendChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: ChatRole
    content: str
    created_at: datetime


class ChatSessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    question_id: int | None
    created_at: datetime
    updated_at: datetime


class ChatSessionDetail(ChatSessionSummary):
    messages: list[ChatMessageResponse]


class SendChatMessageResponse(BaseModel):
    message: ChatMessageResponse
    follow_up_suggestions: list[str] = Field(default_factory=list)
