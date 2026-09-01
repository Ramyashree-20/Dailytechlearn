"""Classifies a SourceArticle against our curated Category/Topic taxonomy
using Groq. This is a RECOMMENDATION — see Phase 10 notes in
docs/architecture.md. Nothing here writes to Category, Topic, or
SourceArticle; the model is told our real taxonomy and asked to pick from
it, but its answer is validated for shape only, never assumed to match a
real row (see ClassificationResult in the router).
"""

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.schemas.content_classification import ContentClassification
from app.services.ai_service import AIServiceError, call_groq_json

SYSTEM_PROMPT = """You are classifying technical articles for DailyTechLearn, \
an app that teaches AI/software engineers.

You will be given (1) our existing Category/Topic taxonomy and (2) one \
article's title, description, and tags.

Pick the SINGLE best-fitting category and topic FROM THE PROVIDED LIST ONLY \
— copy the names exactly as given. Do not invent new category or topic \
names. If nothing fits well, pick the closest match.

Return a JSON object with EXACTLY these fields:
- "category": the chosen category name, copied exactly from the list
- "topic": the chosen topic name, copied exactly from the list
- "difficulty": one of "beginner", "intermediate", "advanced"
- "relevance_score": an integer 1-5 rating how useful this content is for a \
working AI/software engineer (5 = core professional knowledge, 1 = low \
relevance) — judge usefulness, NOT popularity or recency
- "reasoning": one short sentence explaining the choice

Return ONLY the JSON object. No markdown, no commentary outside the JSON.
"""


def _build_taxonomy_listing(db: Session) -> str:
    topics = (
        db.query(Topic)
        .filter(Topic.active.is_(True))
        .order_by(Topic.category_id, Topic.name)
        .all()
    )
    lines = [
        f"- Category: {t.category.name if t.category else 'Uncategorized'} | Topic: {t.name}"
        for t in topics
    ]
    return "\n".join(lines)


def classify_article(db: Session, title: str, description: str, tags: str) -> ContentClassification:
    taxonomy = _build_taxonomy_listing(db)
    user_prompt = (
        f"Existing taxonomy:\n{taxonomy}\n\n"
        f"Article to classify:\nTitle: {title}\nDescription: {description}\nTags: {tags}"
    )

    parsed = call_groq_json(SYSTEM_PROMPT, user_prompt)

    try:
        return ContentClassification.model_validate(parsed)
    except ValidationError as exc:
        raise AIServiceError("Groq's classification didn't match the expected structure") from exc
