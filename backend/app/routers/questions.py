from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.question import Question
from app.models.topic import Topic
from app.schemas.question import QuestionCreate, QuestionResponse
from app.services.auth_service import get_current_admin_user

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("", response_model=list[QuestionResponse])
def list_questions(
    topic_id: int | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Question)
    if topic_id is not None:
        query = query.filter(Question.topic_id == topic_id)
    return query.order_by(Question.id).offset(offset).limit(limit).all()


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(question_id: int, db: Session = Depends(get_db)):
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post(
    "", response_model=QuestionResponse, status_code=201, dependencies=[Depends(get_current_admin_user)]
)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    topic = db.get(Topic, payload.topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    question = Question(**payload.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question
