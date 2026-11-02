from sqlalchemy.orm import Session
from uuid import UUID

from models.lab_category import LabCategory as LabCategoryModel
from schemas.lab_category import LabCategoryCreate, LabCategoryUpdate

def create_category(db: Session, item: LabCategoryCreate, context_tenant_id: UUID = None):
    db_item = LabCategoryModel(**item.model_dump(), tenant_id=context_tenant_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(LabCategoryModel).offset(skip).limit(limit).all()

def get_category(db: Session, item_id: UUID):
    return db.query(LabCategoryModel).filter(LabCategoryModel.id == item_id).first()

def update_category(db: Session, db_item: LabCategoryModel, item_update: LabCategoryUpdate):
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_category(db: Session, db_item: LabCategoryModel):
    db.delete(db_item)
    db.commit()
