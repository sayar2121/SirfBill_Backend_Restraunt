from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from schemas.lab_category import LabCategoryCreate, LabCategoryUpdate, LabCategoryResponse
from crud import lab_category as crud_lab_category
from models.database import get_db
from dependencies import get_admin_user
from models.user import User

router = APIRouter(
    prefix="/api/admin/lab-category",
    tags=["Admin - Lab Categories"]
)

@router.post("/", response_model=LabCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_lab_category(
    item: LabCategoryCreate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: Add a new lab category.
    """
    return crud_lab_category.create_category(db=db, item=item, context_tenant_id=admin_user.tenant_id)

@router.get("/", response_model=List[LabCategoryResponse])
def get_lab_categories(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: List all lab categories.
    """
    return crud_lab_category.get_categories(db, skip=skip, limit=limit)

@router.get("/{item_id}", response_model=LabCategoryResponse)
def get_lab_category(
    item_id: UUID, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: Get a specific lab category.
    """
    db_item = crud_lab_category.get_category(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Lab category not found")
    return db_item

@router.patch("/{item_id}", response_model=LabCategoryResponse)
def update_lab_category(
    item_id: UUID, 
    item_update: LabCategoryUpdate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: Update an existing lab category.
    """
    db_item = crud_lab_category.get_category(db, item_id=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Lab category not found"
        )
    
    return crud_lab_category.update_category(db=db, db_item=db_item, item_update=item_update)

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lab_category(
    item_id: UUID, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: Remove a lab category.
    """
    db_item = crud_lab_category.get_category(db, item_id=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Lab category not found"
        )
    
    crud_lab_category.delete_category(db=db, db_item=db_item)
    return None
