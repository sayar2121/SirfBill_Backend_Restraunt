from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from models.database import get_db
from schemas.print_job import PrintJobOut, PrintJobCreate, PrintJobUpdate
from crud import print_job as crud_print_job

router = APIRouter(prefix="/api/admin/print-jobs", tags=["print_jobs"])

@router.get("/shop/{shop_id}", response_model=List[PrintJobOut])
def read_print_jobs(shop_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_print_job.get_print_jobs(db, shop_id=shop_id, skip=skip, limit=limit)

@router.post("/", response_model=PrintJobOut)
def create_print_job(job: PrintJobCreate, db: Session = Depends(get_db)):
    return crud_print_job.create_print_job(db=db, print_job=job)

@router.put("/{job_id}", response_model=PrintJobOut)
def update_print_job(job_id: UUID, job: PrintJobUpdate, db: Session = Depends(get_db)):
    db_job = crud_print_job.update_print_job(db, job_id=job_id, print_job=job)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Print job not found")
    return db_job

@router.delete("/{job_id}")
def delete_print_job(job_id: UUID, db: Session = Depends(get_db)):
    success = crud_print_job.delete_print_job(db, job_id=job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Print job not found")
    return {"message": "Print job deleted successfully"}
