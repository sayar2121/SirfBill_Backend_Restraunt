from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from models.doctor import Doctor
from schemas.doctor import DoctorCreate, DoctorUpdate

def get_doctor(db: Session, doctor_id: UUID) -> Optional[Doctor]:
    return db.query(Doctor).filter(Doctor.id == doctor_id).first()

def get_doctors(db: Session, skip: int = 0, limit: int = 100) -> List[Doctor]:
    return db.query(Doctor).offset(skip).limit(limit).all()

def create_doctor(db: Session, doctor: DoctorCreate, context_tenant_id: Optional[UUID] = None) -> Doctor:
    doctor_data = doctor.model_dump()
    if context_tenant_id:
        doctor_data["tenant_id"] = context_tenant_id
    db_doctor = Doctor(**doctor_data)
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

def update_doctor(db: Session, db_doctor: Doctor, doctor_update: DoctorUpdate) -> Doctor:
    update_data = doctor_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_doctor, key, value)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

def delete_doctor(db: Session, db_doctor: Doctor) -> Doctor:
    db.delete(db_doctor)
    db.commit()
    return db_doctor
