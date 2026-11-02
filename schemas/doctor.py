from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class DoctorBase(BaseModel):
    tenant_id: Optional[UUID] = None
    name: str
    specialty_key: str
    experience: Optional[str] = None
    fee: float
    image_url: Optional[str] = None
    about: Optional[str] = None

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialty_key: Optional[str] = None
    experience: Optional[str] = None
    fee: Optional[float] = None
    image_url: Optional[str] = None
    about: Optional[str] = None

class Doctor(DoctorBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
