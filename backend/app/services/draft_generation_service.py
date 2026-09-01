"""Orchestrates turning one eligible SourceArticle into an AIDraft:
eligibility check (content_selection_service) -> Groq generation
(question_generation_service) -> AIDraft row. Never creates a Question —
the Phase 9 approval boundary is untouched; nothing here bypasses it.
"""

from sqlalchemy.orm import Session

from app.config import GROQ_MODEL
from app.models.ai_draft import AIDraft
from app.models.source_article import SourceArticle
from app.services.content_selection_service import is_eligible
from app.services.question_generation_service import generate_content_for_article


class DraftGenerationError(Exception):
    """Raised when an article can't produce a draft right now — e.g. it's
    not (or no longer) an eligible candidate. Carries the HTTP status code
    the router should respond with."""

    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code


def generate_learning_draft(db: Session, article: SourceArticle) -> AIDraft:
    if not is_eligible(db, article):
        raise DraftGenerationError(
            f"Source article {article.id} is not an eligible candidate right now "
            "(not classified, already has an approved/unreviewed draft, or its topic is inactive)"
        )

    topic_name = article.classified_topic.name if article.classified_topic else "Unclassified"
    generated = generate_content_for_article(article, topic_name)  # raises AIServiceError on Groq failure

    draft = AIDraft(
        source_article_id=article.id,
        question_text=generated.question,
        answer=generated.answer,
        simple_explanation=generated.simple_explanation,
        real_world_example=generated.real_world_example,
        business_relevance=generated.business_relevance,
        difficulty=generated.difficulty,
        keywords=generated.keywords,
        model_name=GROQ_MODEL,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft
