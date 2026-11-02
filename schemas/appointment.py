from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from models.enums import BookingStatus

class AppointmentBase(BaseModel):
    tenant_id: Optional[UUID] = None
    user_id: UUID
    doctor_id: Optional[UUID] = None
    status: BookingStatus = BookingStatus.PENDING_CONFIRMATION
    preferred_date: date
    form_details: Optional[Any] = None
    prescription_url: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    user_id: Optional[UUID] = None
    doctor_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None  # ADDED: To assign staff
    admin_notes: Optional[str] = None # ADDED: Internal use only
    status: Optional[BookingStatus] = None
    preferred_date: Optional[date] = None
    form_details: Optional[Any] = None
    prescription_url: Optional[str] = None

class Appointment(AppointmentBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
