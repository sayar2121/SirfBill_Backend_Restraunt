from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from models.database import get_db
from schemas.rack import RackOut, RackCreate, RackUpdate
from crud import rack as crud_rack

router = APIRouter(prefix="/api/admin/racks", tags=["racks"])

@router.get("/shop/{shop_id}", response_model=List[RackOut])
def read_racks(shop_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    racks = crud_rack.get_racks(db, shop_id=shop_id, skip=skip, limit=limit)
    return racks

@router.post("/", response_model=RackOut)
def create_rack(rack: RackCreate, db: Session = Depends(get_db)):
    return crud_rack.create_rack(db=db, rack=rack)

@router.put("/{rack_id}", response_model=RackOut)
def update_rack(rack_id: UUID, rack: RackUpdate, db: Session = Depends(get_db)):
    db_rack = crud_rack.update_rack(db, rack_id=rack_id, rack=rack)
    if db_rack is None:
        raise HTTPException(status_code=404, detail="Rack not found")
    return db_rack

@router.delete("/{rack_id}")
def delete_rack(rack_id: UUID, db: Session = Depends(get_db)):
    success = crud_rack.delete_rack(db, rack_id=rack_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rack not found")
    return {"message": "Rack deleted successfully"}
