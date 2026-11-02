from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from models.transaction_category import TransactionCategory
from schemas.transaction_category import TransactionCategoryCreate, TransactionCategoryUpdate

def get_transaction_category(db: Session, category_id: UUID) -> Optional[TransactionCategory]:
    return db.query(TransactionCategory).filter(TransactionCategory.id == category_id).first()

def get_transaction_categories(db: Session, skip: int = 0, limit: int = 100) -> List[TransactionCategory]:
    return db.query(TransactionCategory).offset(skip).limit(limit).all()

def create_transaction_category(db: Session, category: TransactionCategoryCreate, context_tenant_id: Optional[UUID] = None) -> TransactionCategory:
    category_data = category.model_dump()
    if context_tenant_id:
        category_data["tenant_id"] = context_tenant_id
    db_category = TransactionCategory(**category_data)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_transaction_category(db: Session, db_category: TransactionCategory, category_update: TransactionCategoryUpdate) -> TransactionCategory:
    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_transaction_category(db: Session, db_category: TransactionCategory) -> TransactionCategory:
    db.delete(db_category)
    db.commit()
    return db_category
