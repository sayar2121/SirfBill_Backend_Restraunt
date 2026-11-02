from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from schemas.transaction_category import TransactionCategoryCreate, TransactionCategoryUpdate, TransactionCategoryResponse
from crud import transaction_category as crud_transaction_category
from models.database import get_db

router = APIRouter(
    prefix="/api/transaction-categories",
    tags=["Transaction Categories"]
)

@router.get("", response_model=List[TransactionCategoryResponse])
def get_transaction_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_transaction_category.get_transaction_categories(db, skip=skip, limit=limit)

@router.post("", response_model=TransactionCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_transaction_category(category: TransactionCategoryCreate, db: Session = Depends(get_db)):
    return crud_transaction_category.create_transaction_category(db=db, category=category)

@router.get("/{category_id}", response_model=TransactionCategoryResponse)
def get_transaction_category(category_id: UUID, db: Session = Depends(get_db)):
    db_category = crud_transaction_category.get_transaction_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Transaction Category not found")
    return db_category

@router.patch("/{category_id}", response_model=TransactionCategoryResponse)
def update_transaction_category(category_id: UUID, category_update: TransactionCategoryUpdate, db: Session = Depends(get_db)):
    db_category = crud_transaction_category.get_transaction_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Transaction Category not found")
    return crud_transaction_category.update_transaction_category(db=db, db_category=db_category, category_update=category_update)

@router.delete("/{category_id}", response_model=TransactionCategoryResponse)
def delete_transaction_category(category_id: UUID, db: Session = Depends(get_db)):
    db_category = crud_transaction_category.get_transaction_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Transaction Category not found")
    return crud_transaction_category.delete_transaction_category(db=db, db_category=db_category)
