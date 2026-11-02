from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
import os
import aiofiles

from schemas.story import StoryCreate, StoryUpdate, Story as StorySchema
from crud import story as crud_story
from models.database import get_db

from dependencies import get_admin_user
from models.user import User

router = APIRouter(
    prefix="/api",
    tags=["Stories (Testimonials)"]
)

@router.post("/admin/stories", response_model=StorySchema, status_code=status.HTTP_201_CREATED)
async def upload_story(
    caption: str = Form(None),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED: Admin Only!
):
    """
    Admin Action: Upload a new video or image testimonial.
    This saves the file locally and creates the database record simultaneously.
    """
    # Validate file type (Images and Videos)
    valid_extensions = ('.mp4', '.mov', '.jpg', '.jpeg', '.png')
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Please upload an image or video."
        )

    # Determine media type for the database
    media_type = "VIDEO" if file.filename.lower().endswith(('.mp4', '.mov')) else "IMAGE"

    # Create the upload directory safely
    upload_dir = "./uploads/stories"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate a unique temporary ID for the filename
    import uuid
    temp_id = uuid.uuid4()
    file_extension = file.filename.split(".")[-1]
    file_path = f"{upload_dir}/story_{temp_id}.{file_extension}"
    
    # Save the file asynchronously
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # Create the database record
    public_url = f"/uploads/stories/story_{temp_id}.{file_extension}"
    
    story_data = StoryCreate(
        media_type=media_type,
        media_url=public_url,
        caption=caption,
        view_count=0
    )
    
    return crud_story.create_story(db=db, story=story_data)

@router.get("/stories", response_model=list[StorySchema])
def get_stories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Public/App Action: Fetch the list of available stories (testimonials).
    """
    return crud_story.get_stories(db, skip=skip, limit=limit)


@router.patch("/stories/{story_id}/view", response_model=StorySchema)
def increment_story_view(story_id: UUID, db: Session = Depends(get_db)):
    """
    Public/App Action: Increments the view count of a story when a user watches it.
    """
    db_story = crud_story.get_story(db, story_id=story_id)
    if not db_story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Increment view count
    new_count = db_story.view_count + 1
    story_update = StoryUpdate(view_count=new_count)
    
    return crud_story.update_story(db=db, db_story=db_story, story_update=story_update)

@router.delete("/admin/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(
    story_id: UUID, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin Action: Remove a story from the feed.
    """
    db_story = crud_story.get_story(db, story_id=story_id)
    if not db_story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    crud_story.delete_story(db=db, db_story=db_story)
    # Note: In a true production app, you might also want to delete the local file using os.remove()
    return None
