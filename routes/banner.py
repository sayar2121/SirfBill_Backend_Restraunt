from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
import os
import aiofiles

from models.database import get_db
from dependencies import get_admin_user
from models.user import User
from models.banner import Banner

router = APIRouter(
    prefix="/api/admin/banners",
    tags=["Admin - Banners"]
)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_banner(
    action_url: str = Form(None),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin Action: Upload a new advertisement banner for the app home screen.
    """
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        raise HTTPException(status_code=400, detail="Invalid image format.")

    upload_dir = "./uploads/banners"
    os.makedirs(upload_dir, exist_ok=True)

    import uuid
    temp_id = uuid.uuid4()
    file_extension = file.filename.split(".")[-1]
    file_path = f"{upload_dir}/banner_{temp_id}.{file_extension}"
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    public_url = f"/uploads/banners/banner_{temp_id}.{file_extension}"
    
    new_banner = Banner(
        image_url=public_url,
        action_url=action_url,
        is_active=True
    )
    db.add(new_banner)
    db.commit()
    db.refresh(new_banner)
    
    return {"message": "Banner uploaded successfully", "banner_id": new_banner.id, "image_url": public_url}

@router.delete("/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_banner(
    banner_id: UUID, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin Action: Remove an advertisement banner.
    """
    db_banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not db_banner:
        raise HTTPException(status_code=404, detail="Banner not found")
        
    db.delete(db_banner)
    db.commit()
    return None
