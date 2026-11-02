from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class MachineBase(BaseModel):
    name: str
    model_number: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    current_ink_level: Optional[str] = None
    is_active: Optional[bool] = True

class MachineCreate(MachineBase):
    shop_id: UUID

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    model_number: Optional[str] = None
    status: Optional[str] = None
    current_ink_level: Optional[str] = None
    is_active: Optional[bool] = None

class MachineOut(MachineBase):
    id: UUID
    shop_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
