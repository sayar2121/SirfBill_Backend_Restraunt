from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class DistributorBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class DistributorCreate(DistributorBase):
    shop_id: UUID

class DistributorUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class DistributorOut(DistributorBase):
    id: UUID
    shop_id: UUID
    tenant_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
