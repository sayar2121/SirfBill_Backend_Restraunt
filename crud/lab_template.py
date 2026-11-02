from sqlalchemy.orm import Session
from models.lab_template import LabTemplate as LabTemplateModel
from schemas.lab_template import LabTemplateCreate, LabTemplateUpdate

def camel_to_snake(name: str) -> str:
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

def create_lab_template(db: Session, item: LabTemplateCreate):
    data = item.model_dump() if hasattr(item, 'model_dump') else item.dict()
    snake_data = {camel_to_snake(k): v for k, v in data.items()}
    db_item = LabTemplateModel(**snake_data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_lab_templates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(LabTemplateModel).offset(skip).limit(limit).all()

def get_lab_template(db: Session, item_id: str):
    return db.query(LabTemplateModel).filter(LabTemplateModel.id == item_id).first()

def update_lab_template(db: Session, db_item: LabTemplateModel, item_update: LabTemplateUpdate):
    update_data = item_update.model_dump(exclude_unset=True) if hasattr(item_update, 'model_dump') else item_update.dict(exclude_unset=True)
    snake_data = {camel_to_snake(k): v for k, v in update_data.items()}
    
    for key, value in snake_data.items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_lab_template(db: Session, db_item: LabTemplateModel):
    db.delete(db_item)
    db.commit()
