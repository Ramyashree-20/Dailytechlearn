"""Decides which classified SourceArticles are worth turning into a new
AI draft right now. Purely deterministic backend logic — Groq is never
asked "is this worth learning," only used earlier (classification) and
later (generation) in the pipeline. See Phase 11 notes in
docs/architecture.md.

Two steps, kept separate:
1. Eligibility — a yes/no filter (is_eligible). Disqualifies articles that
   can't be candidates at all, for clear structural reasons.
2. Scoring — only applied to what survives eligibility. Ranks candidates so
   the "best" ones are picked first, out of what's already allowed.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ai_draft import AIDraft, DraftStatus
from app.models.source_article import SourceArticle
from app.models.topic import Topic

# A relevance_score of 1 ("low relevance" on Phase 10's 1-5 scale) is
# excluded from ever becoming a candidate. Adjustable — not scientific truth.
MIN_RELEVANCE_SCORE = 2

# Linear freshness decay: 1.0 at 0 days old, 0.0 at this many days or older.
# A placeholder policy, not a scientifically tuned curve.
FRESHNESS_DECAY_DAYS = 90

# Selection score weights — an initial product decision (see Phase 11
# notes), deliberately NOT scientific truth. Freshness is weighted lowest on
# purpose: a two-year-old "What is an API?" article can still matter more
# than something merely recent. LearningProgress/personalization is
# intentionally NOT part of this score yet — see docs/architecture.md for
# where that will plug in later.
IMPORTANCE_WEIGHT = 0.40
RELEVANCE_WEIGHT = 0.40
FRESHNESS_WEIGHT = 0.20


@dataclass
class Candidate:
    article: SourceArticle
    topic: Topic
    importance_score: float
    relevance_score: float
    freshness_score: float
    selection_score: float


def _normalize_1_to_5(value: int) -> float:
    """Maps a 1-5 scale to 0-1, with 1 -> 0.0 and 5 -> 1.0."""
    return (value - 1) / 4


def _freshness_score(article: SourceArticle) -> float:
    reference_date = article.published_at or article.fetched_at
    if reference_date is None:
        return 0.0
    age_days = (datetime.now(timezone.utc) - reference_date).total_seconds() / 86400
    return max(0.0, 1 - age_days / FRESHNESS_DECAY_DAYS)


def is_eligible(db: Session, article: SourceArticle) -> bool:
    """Deterministic yes/no filter — see Step 6 rules in Phase 11 notes."""
    if (
        article.classified_category_id is None
        or article.classified_topic_id is None
        or article.classified_difficulty is None
        or article.relevance_score is None
    ):
        return False  # not classified (or classification incomplete)

    if article.relevance_score < MIN_RELEVANCE_SCORE:
        return False  # too low-value to bother with

    topic = db.get(Topic, article.classified_topic_id)
    if topic is None or not topic.active:
        return False  # topic paused or somehow missing

    existing_drafts = db.query(AIDraft).filter(AIDraft.source_article_id == article.id).all()
    if any(d.status == DraftStatus.APPROVED for d in existing_drafts):
        return False  # already produced a real Question
    if any(d.status == DraftStatus.GENERATED for d in existing_drafts):
        return False  # already has an unreviewed draft awaiting a decision

    return True


def count_eligible_candidates(db: Session) -> int:
    """How many SourceArticles are currently eligible, without scoring or
    ranking them — cheaper than get_candidates() when only a count is
    needed (e.g. for the Phase 13 pipeline-status endpoint)."""
    articles = db.query(SourceArticle).all()
    return sum(1 for article in articles if is_eligible(db, article))


def get_candidates(db: Session, limit: int = 10) -> list[Candidate]:
    """Eligible articles, scored and ranked (best first), deterministically."""
    articles = db.query(SourceArticle).all()

    candidates: list[Candidate] = []
    for article in articles:
        if not is_eligible(db, article):
            continue

        topic = db.get(Topic, article.classified_topic_id)
        importance = _normalize_1_to_5(topic.importance)
        relevance = _normalize_1_to_5(article.relevance_score)
        freshness = _freshness_score(article)
        score = (
            IMPORTANCE_WEIGHT * importance + RELEVANCE_WEIGHT * relevance + FRESHNESS_WEIGHT * freshness
        )
        candidates.append(Candidate(article, topic, importance, relevance, freshness, score))

    # Deterministic: highest score first, article id as a stable tie-breaker
    # (never random — see Phase 11 notes on why that matters for testing).
    candidates.sort(key=lambda c: (-c.selection_score, c.article.id))
    return candidates[:limit]
