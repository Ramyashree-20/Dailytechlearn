"""Turns fetched ExternalArticle objects into stored SourceArticle rows.

This is the boundary between "information we found" and "information we've
kept" — see Phase 7 notes in docs/architecture.md. It never creates
Questions; that's a deliberate future transformation step.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.source_article import SourceArticle
from app.services.external_api_service import ExternalArticle, fetch_dev_to_articles


def _parse_published_at(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _store_article(db: Session, article: ExternalArticle) -> bool:
    """Create a new row, or refresh fetched_at on an existing one.

    Returns True if a new row was created, False if it already existed.
    """
    existing = (
        db.query(SourceArticle)
        .filter(
            SourceArticle.source_name == article.source,
            SourceArticle.external_id == article.external_id,
        )
        .first()
    )

    if existing is not None:
        existing.fetched_at = datetime.now(timezone.utc)
        return False

    db.add(
        SourceArticle(
            source_name=article.source,
            external_id=article.external_id,
            title=article.title,
            description=article.description,
            url=article.url,
            tags=", ".join(article.tags) if article.tags else None,
            published_at=_parse_published_at(article.published_at),
        )
    )
    return True


def ingest_dev_to_articles(db: Session, tag: str = "programming", limit: int = 5) -> dict[str, int]:
    articles = fetch_dev_to_articles(tag=tag, limit=limit)

    created = 0
    skipped_duplicates = 0
    seen_this_run: set[tuple[str, str]] = set()

    for article in articles:
        key = (article.source, article.external_id)
        if key in seen_this_run:
            # The external API returned the same article twice in one
            # fetch — still results in only one database record.
            skipped_duplicates += 1
            continue
        seen_this_run.add(key)

        if _store_article(db, article):
            created += 1
        else:
            skipped_duplicates += 1

    db.commit()

    return {
        "fetched": len(articles),
        "created": created,
        "skipped_duplicates": skipped_duplicates,
    }
