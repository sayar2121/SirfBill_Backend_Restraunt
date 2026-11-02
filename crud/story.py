from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from models.story import Story
from schemas.story import StoryCreate, StoryUpdate

def get_story(db: Session, story_id: UUID) -> Optional[Story]:
    return db.query(Story).filter(Story.id == story_id).first()

def get_stories(db: Session, skip: int = 0, limit: int = 100) -> List[Story]:
    return db.query(Story).offset(skip).limit(limit).all()

def create_story(db: Session, story: StoryCreate, context_tenant_id: Optional[UUID] = None) -> Story:
    story_data = story.model_dump()
    if context_tenant_id:
        story_data["tenant_id"] = context_tenant_id
    db_story = Story(**story_data)
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    return db_story

def update_story(db: Session, db_story: Story, story_update: StoryUpdate) -> Story:
    update_data = story_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_story, key, value)
    db.commit()
    db.refresh(db_story)
    return db_story

def delete_story(db: Session, db_story: Story) -> Story:
    db.delete(db_story)
    db.commit()
    return db_story
