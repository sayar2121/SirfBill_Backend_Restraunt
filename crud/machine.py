from sqlalchemy.orm import Session
from uuid import UUID
from models.machine import Machine
from schemas.machine import MachineCreate, MachineUpdate

def get_machines(db: Session, shop_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(Machine).filter(Machine.shop_id == shop_id).offset(skip).limit(limit).all()

def create_machine(db: Session, machine: MachineCreate):
    db_machine = Machine(**machine.model_dump())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

def update_machine(db: Session, machine_id: UUID, machine: MachineUpdate):
    db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if db_machine:
        update_data = machine.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_machine, key, value)
        db.commit()
        db.refresh(db_machine)
    return db_machine

def delete_machine(db: Session, machine_id: UUID):
    db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if db_machine:
        db.delete(db_machine)
        db.commit()
        return True
    return False
