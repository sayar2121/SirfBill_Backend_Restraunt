from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from models.database import get_db
from schemas.print_service import PrintServiceOut, PrintServiceCreate, PrintServiceUpdate
from crud import print_service as crud_print_service

router = APIRouter(prefix="/api/admin/print-services", tags=["print_services"])

@router.get("/shop/{shop_id}", response_model=List[PrintServiceOut])
def read_print_services(shop_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_print_service.get_print_services(db, shop_id=shop_id, skip=skip, limit=limit)

@router.post("/", response_model=PrintServiceOut)
def create_print_service(service: PrintServiceCreate, db: Session = Depends(get_db)):
    return crud_print_service.create_print_service(db=db, print_service=service)

@router.put("/{service_id}", response_model=PrintServiceOut)
def update_print_service(service_id: UUID, service: PrintServiceUpdate, db: Session = Depends(get_db)):
    db_service = crud_print_service.update_print_service(db, service_id=service_id, print_service=service)
    if db_service is None:
        raise HTTPException(status_code=404, detail="Print service not found")
    return db_service

@router.delete("/{service_id}")
def delete_print_service(service_id: UUID, db: Session = Depends(get_db)):
    success = crud_print_service.delete_print_service(db, service_id=service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Print service not found")
    return {"message": "Print service deleted successfully"}
