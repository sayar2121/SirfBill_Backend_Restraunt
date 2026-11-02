from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

# Order Line Schemas
class OrderLineModifierInput(BaseModel):
    modifier_option_id: UUID
    name: str
    price: Decimal = Decimal("0.00")

class RestaurantOrderLineCreate(BaseModel):
    item_id: Optional[UUID] = None
    menu_item_id: Optional[Any] = None
    name: Optional[str] = None
    variant_name: str = "Standard"
    quantity: int = Field(1, ge=1)
    unit_price: Optional[Decimal] = None
    price: Optional[Decimal] = None
    notes: Optional[str] = None
    special_instructions: Optional[str] = None
    modifiers: List[OrderLineModifierInput] = []

    model_config = ConfigDict(extra="allow")

class RestaurantOrderLineResponse(BaseModel):
    id: UUID
    order_id: UUID
    item_id: Optional[UUID] = None
    item_name: str
    variant_name: str
    prep_station: str
    quantity: int
    unit_price: Decimal
    modifier_price: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    selected_modifiers: Optional[List[Dict[str, Any]]] = None
    special_instructions: Optional[str] = None
    kot_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Order Schemas
class RestaurantOrderCreate(BaseModel):
    outlet_id: Optional[UUID] = None
    order_type: str = "DINE_IN" # DINE_IN, TAKEAWAY, DELIVERY
    table_id: Optional[Any] = None
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    notes: Optional[str] = None
    payment_method: Optional[str] = "CASH" # CASH, UPI, CARD, DUE
    idempotency_key: Optional[str] = None
    lines: List[RestaurantOrderLineCreate] = []
    items: List[RestaurantOrderLineCreate] = []

    model_config = ConfigDict(extra="allow")

class RestaurantOpenTableOrder(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    notes: Optional[str] = None
    idempotency_key: Optional[str] = None

class RestaurantOrderUpdateItems(BaseModel):
    expected_version: int = Field(..., description="Optimistic locking version check")
    lines: List[RestaurantOrderLineCreate]

class RestaurantApplyDiscount(BaseModel):
    expected_version: int = Field(..., description="Optimistic locking version check")
    discount_amount: Decimal = Field(..., ge=0)
    discount_reason: str = Field(..., min_length=3)

class RestaurantOrderStateTransition(BaseModel):
    status: Optional[str] = None # DRAFT, OPEN, SENT_TO_KITCHEN, COMPLETED, CANCELLED, VOIDED
    target_status: Optional[str] = None
    reason: Optional[str] = None
    expected_version: Optional[int] = None

    model_config = ConfigDict(extra="allow")


class RestaurantOrderResponse(BaseModel):
    id: UUID
    outlet_id: UUID
    tenant_id: UUID
    order_number: str
    order_type: str
    status: str
    table_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    waiter_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None
    subtotal: Decimal
    discount_amount: Decimal
    discount_reason: Optional[str] = None
    tax_amount: Decimal
    rounding_adjustment: Decimal
    grand_total: Decimal
    paid_amount: Decimal
    payment_method: Optional[str] = "CASH"
    notes: Optional[str] = None
    version: int
    idempotency_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: List[RestaurantOrderLineResponse] = []

    model_config = ConfigDict(from_attributes=True)
