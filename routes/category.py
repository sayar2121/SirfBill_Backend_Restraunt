from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from models.database import get_db
from schemas.category import CategoryOut, CategoryCreate, CategoryUpdate
from crud import category as crud_category

router = APIRouter(prefix="/api/admin/categories", tags=["categories"])

@router.get("/shop/{shop_id}", response_model=List[CategoryOut])
def read_categories(shop_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = crud_category.get_categories(db, shop_id=shop_id, skip=skip, limit=limit)
    return categories

@router.post("/", response_model=CategoryOut)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    return crud_category.create_category(db=db, category=category)

@router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: UUID, category: CategoryUpdate, db: Session = Depends(get_db)):
    db_category = crud_category.update_category(db, category_id=category_id, category=category)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.delete("/{category_id}")
def delete_category(category_id: UUID, db: Session = Depends(get_db)):
    success = crud_category.delete_category(db, category_id=category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}
