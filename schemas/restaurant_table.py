from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class RestaurantTableBase(BaseModel):
    table_code: Optional[str] = None
    table_number: Optional[str] = None
    section: Optional[str] = "Main Hall"
    floor: Optional[str] = None
    capacity: int = Field(4, ge=1)
    status: str = "VACANT" # VACANT, OCCUPIED, RESERVED, CLEANING, AVAILABLE
    is_active: bool = True

    model_config = ConfigDict(extra="allow", from_attributes=True)

class RestaurantTableCreate(RestaurantTableBase):
    outlet_id: Optional[UUID] = None

class RestaurantTableUpdate(BaseModel):
    table_code: Optional[str] = None
    table_number: Optional[str] = None
    section: Optional[str] = None
    floor: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="allow")

class RestaurantTableResponse(RestaurantTableBase):
    id: UUID
    outlet_id: UUID
    tenant_id: UUID
    active_order_id: Optional[UUID] = None
    active_order_number: Optional[str] = None
    active_order_status: Optional[str] = None
    active_order_created_at: Optional[datetime] = None
    active_order_grand_total: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
