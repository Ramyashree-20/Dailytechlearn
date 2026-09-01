"""Fetches raw information from external sources.

This is an INFORMATION SOURCE, not our application's database — see Phase 6
notes in docs/architecture.md. Nothing returned here is saved to PostgreSQL
yet; a future phase will decide what's worth turning into real Question rows.

Currently wraps one source (Dev.to's public articles API). Anything calling
into this module works with the normalized `ExternalArticle` shape below, not
Dev.to's raw response — so adding a second source later means adding another
fetch function that returns the same shape, not rewriting every caller.
"""

import httpx
from pydantic import BaseModel

from app.config import DEV_TO_API_BASE_URL

REQUEST_TIMEOUT_SECONDS = 5.0


class ExternalArticle(BaseModel):
    source: str
    external_id: str
    title: str
    url: str
    description: str | None
    tags: list[str]
    published_at: str | None


class ExternalAPIError(Exception):
    """Raised when an external source can't be reached or returns something unusable."""


def fetch_dev_to_articles(tag: str = "programming", limit: int = 5) -> list[ExternalArticle]:
    try:
        response = httpx.get(
            f"{DEV_TO_API_BASE_URL}/articles",
            params={"tag": tag, "per_page": limit},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise ExternalAPIError("Dev.to API request timed out") from exc
    except httpx.RequestError as exc:
        raise ExternalAPIError("Could not reach Dev.to API (network error)") from exc
    except httpx.HTTPStatusError as exc:
        raise ExternalAPIError(
            f"Dev.to API returned an error status: {exc.response.status_code}"
        ) from exc

    try:
        raw_articles = response.json()
    except ValueError as exc:
        raise ExternalAPIError("Dev.to API returned invalid JSON") from exc

    return [
        ExternalArticle(
            source="dev.to",
            external_id=str(item["id"]),
            title=item.get("title", ""),
            url=item.get("url", ""),
            description=item.get("description"),
            tags=item.get("tag_list", []),
            published_at=item.get("published_at"),
        )
        for item in raw_articles
    ]
