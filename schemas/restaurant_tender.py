from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class RestaurantTenderCreate(BaseModel):
    method: str = Field(..., max_length=30) # CASH, UPI, CARD, COMPLIMENTARY, DUE
    amount: Decimal = Field(..., gt=0)
    reference: Optional[str] = None
    idempotency_key: Optional[str] = None

class RestaurantTenderResponse(BaseModel):
    id: UUID
    order_id: UUID
    tenant_id: UUID
    method: str
    amount: Decimal
    reference: Optional[str] = None
    status: str
    cashier_id: Optional[UUID] = None
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RestaurantRefundCreate(BaseModel):
    tender_id: UUID
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=3)

class RestaurantRefundResponse(BaseModel):
    id: UUID
    tender_id: UUID
    order_id: UUID
    amount: Decimal
    reason: str
    authorized_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Split Tender Checkout
class TenderItemInput(BaseModel):
    method: str = Field(..., max_length=30) # CASH, UPI, CARD, DUE
    amount: Decimal = Field(..., gt=0)
    reference: Optional[str] = None

class RestaurantMultiTenderCheckout(BaseModel):
    tenders: Optional[list[TenderItemInput]] = None
    payment_splits: Optional[list[TenderItemInput]] = None # alias for tenders
    discount_type: Optional[str] = None # PERCENTAGE, FLAT, NONE
    discount_value: Optional[Decimal] = None
    discount_reason: Optional[str] = "POS Settle Discount"
    idempotency_key: Optional[str] = None

# Receipt / Invoice Schema
class ReceiptLineItem(BaseModel):
    name: str
    variant: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    modifiers: Optional[str] = None

class RestaurantReceiptResponse(BaseModel):
    order_id: UUID
    order_number: str
    order_type: str
    outlet_name: str
    table_code: Optional[str] = None
    cashier_name: Optional[str] = None
    date: datetime
    items: list[ReceiptLineItem]
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    rounding_adjustment: Decimal
    grand_total: Decimal
    paid_amount: Decimal
    change_due: Decimal
    tenders: list[RestaurantTenderResponse]
    is_reprint: bool = False
    reprint_count: int = 0

