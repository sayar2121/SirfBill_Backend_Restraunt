from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from models.database import get_db
from schemas.machine import MachineOut, MachineCreate, MachineUpdate
from crud import machine as crud_machine

router = APIRouter(prefix="/api/admin/machines", tags=["machines"])

@router.get("/shop/{shop_id}", response_model=List[MachineOut])
def read_machines(shop_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_machine.get_machines(db, shop_id=shop_id, skip=skip, limit=limit)

@router.post("/", response_model=MachineOut)
def create_machine(machine: MachineCreate, db: Session = Depends(get_db)):
    return crud_machine.create_machine(db=db, machine=machine)

@router.put("/{machine_id}", response_model=MachineOut)
def update_machine(machine_id: UUID, machine: MachineUpdate, db: Session = Depends(get_db)):
    db_machine = crud_machine.update_machine(db, machine_id=machine_id, machine=machine)
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return db_machine

@router.delete("/{machine_id}")
def delete_machine(machine_id: UUID, db: Session = Depends(get_db)):
    success = crud_machine.delete_machine(db, machine_id=machine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"message": "Machine deleted successfully"}
