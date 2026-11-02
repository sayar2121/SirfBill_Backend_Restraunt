from sqlalchemy.orm import Session
from uuid import UUID
from models.print_job import PrintJob
from schemas.print_job import PrintJobCreate, PrintJobUpdate

def get_print_jobs(db: Session, shop_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(PrintJob).filter(PrintJob.shop_id == shop_id).offset(skip).limit(limit).all()

def create_print_job(db: Session, print_job: PrintJobCreate):
    db_job = PrintJob(**print_job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def update_print_job(db: Session, job_id: UUID, print_job: PrintJobUpdate):
    db_job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if db_job:
        update_data = print_job.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_job, key, value)
        db.commit()
        db.refresh(db_job)
    return db_job

def delete_print_job(db: Session, job_id: UUID):
    db_job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if db_job:
        db.delete(db_job)
        db.commit()
        return True
    return False
