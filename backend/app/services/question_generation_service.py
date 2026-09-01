"""Generates one piece of learning content grounded in one specific
SourceArticle's actual content and classification. Reuses the low-level
Groq-calling plumbing from ai_service.py (Phase 8) — no separate Groq client
setup. Produces a GeneratedLearningContent only; never touches AIDraft or
Question directly (see draft_generation_service.py for that orchestration).
"""

from pydantic import ValidationError

from app.models.source_article import SourceArticle
from app.schemas.ai import GeneratedLearningContent
from app.services.ai_service import AIServiceError, call_groq_json

SYSTEM_PROMPT = """You are a technical writer creating learning content for \
DailyTechLearn, an app that teaches AI/software engineers.

You will be given one article's title, description, tags, and its already- \
classified topic and difficulty. Using ONLY the information provided, write \
one piece of learning content about the core concept the article discusses.

Produce a JSON object with EXACTLY these fields:
- "question": a clear, natural question testing understanding of the core \
concept — do NOT copy the article's title verbatim
- "answer": a correct, concise answer (2-4 sentences), in your own words — \
do not copy article text
- "simple_explanation": an explanation a beginner could follow, avoiding \
unnecessary jargon
- "real_world_example": one concrete, realistic example of the concept in \
practice
- "business_relevance": why this matters to a business or product, in \
plain language
- "difficulty": one of "beginner", "intermediate", "advanced"
- "keywords": a short comma-separated list of relevant keywords, or an \
empty string

Rules:
- Return ONLY the JSON object. No markdown, no commentary outside it.
- Stay grounded in the provided information — do not invent specific facts, \
statistics, or version numbers not implied by it.
- Write genuinely useful learning material, not generic filler that could \
apply to any topic.
"""


def _build_user_prompt(article: SourceArticle, topic_name: str) -> str:
    difficulty = article.classified_difficulty.value if article.classified_difficulty else "unknown"
    return (
        f"Title: {article.title}\n"
        f"Description: {article.description or ''}\n"
        f"Tags: {article.tags or ''}\n"
        f"Classified topic: {topic_name}\n"
        f"Classified difficulty: {difficulty}"
    )


def generate_content_for_article(article: SourceArticle, topic_name: str) -> GeneratedLearningContent:
    parsed = call_groq_json(SYSTEM_PROMPT, _build_user_prompt(article, topic_name))
    try:
        return GeneratedLearningContent.model_validate(parsed)
    except ValidationError as exc:
        raise AIServiceError("Groq's response didn't match the expected structure") from exc
