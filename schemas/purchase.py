from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime, date

class PurchaseBillItemBase(BaseModel):
    inventory_item_id: Optional[UUID] = None
    quantity: int
    free_quantity: int = 0
    unit_price: float
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    selling_price: Optional[float] = None
    discount: float = 0.0
    gst: float = 0.0
    hsn_code: Optional[str] = None
    rack_id: Optional[UUID] = None
    category_id: Optional[UUID] = None

    @field_validator("expiry_date", mode="before")
    @classmethod
    def parse_expiry_date(cls, v: Any):
        if v is None or v == "" or (isinstance(v, str) and not v.strip()):
            return None
        return v

class PurchaseBillItemCreate(PurchaseBillItemBase):
    pass

class PurchaseBillItemOut(PurchaseBillItemBase):
    id: UUID
    bill_id: UUID

    model_config = ConfigDict(from_attributes=True)

class PurchaseBillBase(BaseModel):
    distributor_id: Optional[UUID] = None
    invoice_no: Optional[str] = None
    bill_date: date

    total_amount: float
    subtotal: float = 0.0
    total_discount: float = 0.0
    total_gst: float = 0.0
    amount_paid: float = 0.0

    payment_status: str = "PENDING"
    payment_method: Optional[str] = None

    from pydantic import field_validator
    @field_validator('subtotal', 'total_discount', 'total_gst', 'amount_paid', mode='before')
    @classmethod
    def handle_none_financials(cls, v):
        return 0.0 if v is None else v

class PurchaseBillCreate(PurchaseBillBase):
    shop_id: UUID
    items: List[PurchaseBillItemCreate]

class PurchaseBillOut(PurchaseBillBase):
    id: UUID
    shop_id: UUID
    tenant_id: Optional[UUID] = None
    created_at: datetime
    items: List[PurchaseBillItemOut]

    model_config = ConfigDict(from_attributes=True)

class PayPurchaseBillRequest(BaseModel):
    account_id: Optional[UUID] = None
    payment_method: Optional[str] = "CASH"
