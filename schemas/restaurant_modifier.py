from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

# Options
class RestaurantModifierOptionBase(BaseModel):
    name: str = Field(..., max_length=100)
    price_delta: Decimal = Decimal("0.00")
    is_available: bool = True
    is_active: bool = True

class RestaurantModifierOptionCreate(RestaurantModifierOptionBase):
    pass

class RestaurantModifierOptionResponse(RestaurantModifierOptionBase):
    id: UUID
    group_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Groups
class RestaurantModifierGroupBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    min_selection: int = 0
    max_selection: int = 1
    is_active: bool = True

class RestaurantModifierGroupCreate(RestaurantModifierGroupBase):
    outlet_id: UUID
    options: List[RestaurantModifierOptionCreate] = []

class RestaurantModifierGroupResponse(RestaurantModifierGroupBase):
    id: UUID
    outlet_id: UUID
    tenant_id: UUID
    options: List[RestaurantModifierOptionResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
