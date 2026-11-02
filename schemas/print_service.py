from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class PrintServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    price_per_unit: Optional[float] = 0.0
    service_type: Optional[str] = None
    is_active: Optional[bool] = True

class PrintServiceCreate(PrintServiceBase):
    shop_id: UUID

class PrintServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_per_unit: Optional[float] = None
    service_type: Optional[str] = None
    is_active: Optional[bool] = None

class PrintServiceOut(PrintServiceBase):
    id: UUID
    shop_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
