from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class StoryBase(BaseModel):
    tenant_id: Optional[UUID] = None
    media_type: str
    media_url: str
    caption: Optional[str] = None
    view_count: int = 0

class StoryCreate(StoryBase):
    pass

class StoryUpdate(BaseModel):
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    caption: Optional[str] = None
    view_count: Optional[int] = None

class Story(StoryBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
