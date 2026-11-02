from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from models.lab_catalog import LabCatalog
from schemas.lab_catalog import LabCatalogCreate, LabCatalogUpdate

def get_lab_item(db: Session, item_id: UUID) -> Optional[LabCatalog]:
    return db.query(LabCatalog).filter(LabCatalog.id == item_id).first()

def get_lab_items(db: Session, skip: int = 0, limit: int = 100) -> List[LabCatalog]:
    return db.query(LabCatalog).offset(skip).limit(limit).all()

def create_lab_item(db: Session, item: LabCatalogCreate, context_tenant_id: Optional[UUID] = None) -> LabCatalog:
    item_data = item.model_dump()
    if context_tenant_id:
        item_data["tenant_id"] = context_tenant_id
    db_item = LabCatalog(**item_data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_lab_item(db: Session, db_item: LabCatalog, item_update: LabCatalogUpdate) -> LabCatalog:
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_lab_item(db: Session, db_item: LabCatalog) -> LabCatalog:
    db.delete(db_item)
    db.commit()
    return db_item
