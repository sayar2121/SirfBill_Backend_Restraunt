from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from models.appointment import Appointment
from schemas.appointment import AppointmentCreate, AppointmentUpdate

def get_appointment(db: Session, appointment_id: UUID) -> Optional[Appointment]:
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()

def get_appointments_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Appointment]:
    return db.query(Appointment).filter(Appointment.user_id == user_id).offset(skip).limit(limit).all()

def get_appointments_by_doctor(db: Session, doctor_id: UUID, skip: int = 0, limit: int = 100) -> List[Appointment]:
    return db.query(Appointment).filter(Appointment.doctor_id == doctor_id).offset(skip).limit(limit).all()

def get_appointments(db: Session, skip: int = 0, limit: int = 100) -> List[Appointment]:
    return db.query(Appointment).offset(skip).limit(limit).all()

def create_appointment(db: Session, appointment: AppointmentCreate, context_tenant_id: Optional[UUID] = None) -> Appointment:
    appointment_data = appointment.model_dump()
    if context_tenant_id:
        appointment_data["tenant_id"] = context_tenant_id
    db_appointment = Appointment(**appointment_data)
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def update_appointment(db: Session, db_appointment: Appointment, appointment_update: AppointmentUpdate) -> Appointment:
    update_data = appointment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_appointment, key, value)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def delete_appointment(db: Session, db_appointment: Appointment) -> Appointment:
    db.delete(db_appointment)
    db.commit()
    return db_appointment
