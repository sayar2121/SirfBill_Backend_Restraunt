from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class RestaurantShiftOpen(BaseModel):
    outlet_id: UUID
    opening_cash: Decimal = Decimal("0.00")
    notes: Optional[str] = None

class RestaurantShiftClose(BaseModel):
    counted_cash: Decimal = Field(..., ge=0)
    notes: Optional[str] = None

class RestaurantShiftResponse(BaseModel):
    id: UUID
    outlet_id: UUID
    tenant_id: UUID
    cashier_id: Optional[UUID] = None
    status: str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    opening_cash: Decimal
    counted_cash: Optional[Decimal] = None
    expected_cash: Optional[Decimal] = None
    variance: Optional[Decimal] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
