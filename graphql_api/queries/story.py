import strawberry
from typing import Optional, List
from uuid import UUID

from graphql_api.types.story import StoryType 
from models.story import Story as StoryModel
from models.database import get_db

@strawberry.type
class StoryQuery:
    
    @strawberry.field
    def get_stories(self, limit: int = 20, skip: int = 0) -> List[StoryType]:
        """
        Discovery Query: Fetches the WhatsApp-style story feed.
        The mobile app uses this on the home screen to show active testimonials.
        Orders them by newest first.
        """
        db = next(get_db())
        
        db_stories = (
            db.query(StoryModel)
            .order_by(StoryModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return db_stories

    @strawberry.field
    def get_story_by_id(self, story_id: UUID) -> Optional[StoryType]:
        """
        Detail Query: Fetches a specific story if opened directly via a link.
        """
        db = next(get_db())
        
        db_story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
        
        if not db_story:
            return None
            
        return db_story
