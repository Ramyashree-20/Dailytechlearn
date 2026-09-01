from pydantic import BaseModel, ConfigDict


class TopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    category_id: int | None = None
    importance: int
    active: bool
