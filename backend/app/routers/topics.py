from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.topic import Topic
from app.schemas.topic import TopicResponse

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.get("", response_model=list[TopicResponse])
def list_topics(category_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Topic)
    if category_id is not None:
        query = query.filter(Topic.category_id == category_id)
    return query.order_by(Topic.name).all()


@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic
