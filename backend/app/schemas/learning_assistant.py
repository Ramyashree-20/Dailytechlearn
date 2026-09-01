"""Request/response shapes for the AI Learning Assistant (Phase 15).

Deliberately stateless: `history` is supplied by the caller on every
request and never persisted by the backend — see the "why chat isn't
stored" note in docs/architecture.md. The length caps here exist to keep
every prompt sent to Groq bounded in size (cost/abuse protection), not
because these numbers are meaningful product limits.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_ITEM_LENGTH = 4000
MAX_HISTORY_MESSAGES = 20


class AssistantHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_HISTORY_ITEM_LENGTH)


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    # The DailyTechLearn Question the learner is currently viewing, if any.
    # The client sends only the id — the backend loads the real row from
    # PostgreSQL itself, so a caller can never inject fake question content
    # by pretending it came from the database.
    question_id: int | None = None
    # Prior turns of this conversation, resent by the frontend each call
    # (kept only in browser state) so the assistant can answer follow-ups
    # naturally without the backend storing any chat history.
    history: list[AssistantHistoryMessage] = Field(default_factory=list, max_length=MAX_HISTORY_MESSAGES)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


class AssistantResponse(BaseModel):
    answer: str
    follow_up_suggestions: list[str] = Field(default_factory=list)
