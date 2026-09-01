from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.question import Question
from app.models.user import User
from app.schemas.chat import (
    ChatSessionDetail,
    ChatSessionSummary,
    CreateChatSessionRequest,
    SendChatMessageRequest,
    SendChatMessageResponse,
)
from app.services.ai_service import AIServiceError
from app.services.auth_service import get_current_user
from app.services.chat_service import create_session, delete_session, get_owned_session, get_user_sessions, send_message

router = APIRouter(prefix="/api/learning/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionDetail, status_code=201)
def create_chat_session(
    payload: CreateChatSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = None
    if payload.question_id is not None:
        question = db.get(Question, payload.question_id)
        if question is None:
            raise HTTPException(status_code=404, detail="Question not found")

    return create_session(db, current_user.id, question)


@router.get("/sessions", response_model=list[ChatSessionSummary])
def list_chat_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_sessions(db, current_user.id)


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_chat_session(
    session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session = get_owned_session(db, current_user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.post("/sessions/{session_id}/messages", response_model=SendChatMessageResponse)
def post_chat_message(
    session_id: int,
    payload: SendChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_owned_session(db, current_user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    try:
        assistant_message, suggestions = send_message(db, session, payload.message)
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    return SendChatMessageResponse(message=assistant_message, follow_up_suggestions=suggestions)


@router.delete("/sessions/{session_id}", status_code=204)
def delete_chat_session(
    session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session = get_owned_session(db, current_user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    delete_session(db, session)
