from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class RackBase(BaseModel):
    rack_number: str
    details: Optional[str] = None
    is_active: Optional[bool] = True

class RackCreate(RackBase):
    shop_id: UUID

class RackUpdate(BaseModel):
    rack_number: Optional[str] = None
    details: Optional[str] = None
    is_active: Optional[bool] = None

class RackOut(RackBase):
    id: UUID
    shop_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
