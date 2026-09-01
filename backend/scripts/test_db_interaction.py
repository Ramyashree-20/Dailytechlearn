"""Manual check that SQLAlchemy can read/write Topic and Question, and that
the relationship between them works in both directions.

Requires the schema to already exist — run `alembic upgrade head` first.

Run from backend/: python -m scripts.test_db_interaction
"""

from app.database import SessionLocal
from app.models.question import DifficultyLevel, Question
from app.models.topic import Topic

db = SessionLocal()
try:
    topic = Topic(name="Test Topic", description="Created by test_db_interaction.py")
    db.add(topic)
    db.commit()
    db.refresh(topic)
    print(f"Inserted topic: id={topic.id} name={topic.name!r}")

    question = Question(
        topic_id=topic.id,
        question_text="What is Docker?",
        answer="Docker packages an application and its dependencies into a container.",
        simple_explanation="A container is a lightweight, portable box for running software.",
        real_world_example="A company packages its FastAPI app into a Docker image so it runs the same way on every machine.",
        business_relevance="Docker makes deployments more consistent and reduces 'it works on my machine' bugs.",
        difficulty=DifficultyLevel.BEGINNER,
        keywords="docker, container, deployment",
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    print(f"Inserted question: id={question.id} topic_id={question.topic_id}")

    fetched_question = db.get(Question, question.id)
    print(f"Question -> Topic: {fetched_question.topic.name!r}")

    fetched_topic = db.get(Topic, topic.id)
    print(f"Topic -> Questions: {[q.question_text for q in fetched_topic.questions]}")

    assert fetched_question.topic.id == topic.id
    assert fetched_question in fetched_topic.questions
    print("Relationship verified in both directions.")

    db.delete(fetched_question)
    db.delete(fetched_topic)
    db.commit()
    print("Cleaned up test rows.")
finally:
    db.close()
