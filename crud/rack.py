from sqlalchemy.orm import Session
from models.rack import Rack
from schemas.rack import RackCreate, RackUpdate
from uuid import UUID

def get_racks(db: Session, shop_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(Rack).filter(Rack.shop_id == shop_id).offset(skip).limit(limit).all()

def create_rack(db: Session, rack: RackCreate):
    db_rack = Rack(**rack.model_dump())
    db.add(db_rack)
    db.commit()
    db.refresh(db_rack)
    return db_rack

def update_rack(db: Session, rack_id: UUID, rack: RackUpdate):
    db_rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if db_rack:
        update_data = rack.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_rack, key, value)
        db.commit()
        db.refresh(db_rack)
    return db_rack

def delete_rack(db: Session, rack_id: UUID):
    db_rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if db_rack:
        db.delete(db_rack)
        db.commit()
        return True
    return False
