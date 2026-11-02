from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class RestaurantCustomerBase(BaseModel):
    name: str = Field(..., max_length=150)
    phone: str = Field(..., max_length=20)
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_active: bool = True

class RestaurantCustomerCreate(RestaurantCustomerBase):
    outlet_id: UUID

class RestaurantCustomerResponse(RestaurantCustomerBase):
    id: UUID
    outlet_id: UUID
    tenant_id: UUID
    loyalty_points: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoyaltyPointsAdjustment(BaseModel):
    points_delta: int
    reason: str
    idempotency_key: Optional[str] = None

class LoyaltyLedgerResponse(BaseModel):
    id: UUID
    customer_id: UUID
    points_delta: int
    reason: str
    source_order_id: Optional[UUID] = None
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
