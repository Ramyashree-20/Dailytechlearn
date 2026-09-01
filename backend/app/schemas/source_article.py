from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    external_id: str
    title: str
    description: str | None
    url: str
    tags: str | None
    published_at: datetime | None
    fetched_at: datetime
    created_at: datetime


class IngestionResult(BaseModel):
    fetched: int
    created: int
    skipped_duplicates: int
