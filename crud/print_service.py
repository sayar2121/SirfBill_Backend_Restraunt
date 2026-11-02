from sqlalchemy.orm import Session
from uuid import UUID
from models.print_service import PrintService
from schemas.print_service import PrintServiceCreate, PrintServiceUpdate

def get_print_services(db: Session, shop_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(PrintService).filter(PrintService.shop_id == shop_id).offset(skip).limit(limit).all()

def create_print_service(db: Session, print_service: PrintServiceCreate):
    db_service = PrintService(**print_service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def update_print_service(db: Session, service_id: UUID, print_service: PrintServiceUpdate):
    db_service = db.query(PrintService).filter(PrintService.id == service_id).first()
    if db_service:
        update_data = print_service.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_service, key, value)
        db.commit()
        db.refresh(db_service)
    return db_service

def delete_print_service(db: Session, service_id: UUID):
    db_service = db.query(PrintService).filter(PrintService.id == service_id).first()
    if db_service:
        db.delete(db_service)
        db.commit()
        return True
    return False
