"""Persistent AI chat (Phase 16) — the ChatSession/ChatMessage-backed
upgrade to Phase 15's stateless assistant.

Deliberately does NOT reimplement any Groq/prompt logic: sending a message
calls learning_assistant_service.ask_assistant() — the exact same
function Phase 15's POST /api/learning/assistant uses — so there is still
only one system prompt, one Groq call site, and one place Groq's
error/response handling lives. This module owns only persistence: creating
sessions, loading a bounded window of history, and saving messages
transaction-safely around that call.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage, ChatRole
from app.models.chat_session import ChatSession
from app.models.question import Question
from app.schemas.learning_assistant import AssistantHistoryMessage
from app.services.learning_assistant_service import ask_assistant

# How many of a session's most recent messages are loaded from Postgres and
# offered to the assistant as context. Bounds both the DB read and (with
# learning_assistant_service's own further trimming) the size/cost of every
# Groq call — this is Part E's "reasonable recent window," not a full
# conversation replay. No summarization; just a hard, simple cutoff.
RECENT_MESSAGES_LIMIT = 20

DEFAULT_TITLE = "New chat"
MAX_TITLE_LENGTH = 60


def _derive_title(text: str) -> str:
    """Deterministic title from plain text — no Groq call. Collapses
    whitespace (a multi-line first message shouldn't produce a multi-line
    title) and truncates with an ellipsis if needed."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= MAX_TITLE_LENGTH:
        return cleaned
    return cleaned[: MAX_TITLE_LENGTH - 1].rstrip() + "…"


def create_session(db: Session, user_id: int, question: Question | None) -> ChatSession:
    title = _derive_title(f"About: {question.question_text}") if question else DEFAULT_TITLE
    session = ChatSession(user_id=user_id, question_id=question.id if question else None, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_sessions(db: Session, user_id: int) -> list[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


def get_owned_session(db: Session, user_id: int, session_id: int) -> ChatSession | None:
    """Returns the session only if it belongs to this user. The router
    turns None into a 404 identical to "doesn't exist" — a caller must
    never be able to distinguish "not yours" from "not real" (Part C)."""
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .first()
    )


def delete_session(db: Session, session: ChatSession) -> None:
    db.delete(session)  # cascades to its messages (ORM + DB-level ON DELETE CASCADE)
    db.commit()


def _recent_history(db: Session, session_id: int) -> list[AssistantHistoryMessage]:
    recent = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.desc())
        .limit(RECENT_MESSAGES_LIMIT)
        .all()
    )
    recent.reverse()  # back to chronological order
    return [AssistantHistoryMessage(role=m.role.value, content=m.content) for m in recent]


def send_message(db: Session, session: ChatSession, message: str) -> tuple[ChatMessage, list[str]]:
    """Calls Groq, then — only if that succeeds — persists the user's
    message and the assistant's reply together in one transaction.

    Nothing is written to the database before Groq responds successfully:
    no fake assistant message on failure, no orphaned user-only message,
    and a client retry after a failed call can't create duplicates because
    the failed attempt never touched the database at all.
    """
    history = _recent_history(db, session.id)
    is_first_message = len(history) == 0

    # Raises AIServiceError on any Groq failure — nothing has been added to
    # the session yet at this point, so there's nothing to roll back.
    response = ask_assistant(message, session.question, history)

    user_message = ChatMessage(session_id=session.id, role=ChatRole.USER, content=message)
    assistant_message = ChatMessage(session_id=session.id, role=ChatRole.ASSISTANT, content=response.answer)
    db.add(user_message)
    db.add(assistant_message)

    session.updated_at = datetime.now(timezone.utc)
    if is_first_message:
        session.title = _derive_title(message)

    db.commit()
    db.refresh(assistant_message)
    return assistant_message, response.follow_up_suggestions
