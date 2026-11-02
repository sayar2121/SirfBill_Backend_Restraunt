import strawberry
from typing import Optional
from uuid import UUID
from datetime import datetime

@strawberry.type
class StoryType:
    id: UUID
    media_type: str
    media_url: str
    caption: Optional[str]
    view_count: int
    created_at: datetime
