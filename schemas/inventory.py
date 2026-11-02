from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any
from uuid import UUID
from datetime import date

class InventoryItemBase(BaseModel):
    name: str
    sku: str
    manufacturer: Optional[str] = None
    batch_number: Optional[str] = None
    stock_quantity: int
    loose_stock: int = 0
    pack_size: int = 1
    buying_price: float = 0.0
    hsn_code: Optional[str] = None
    unit_price: float
    expiry_date: Optional[date] = None
    image_url: Optional[str] = None
    gst: Optional[float] = 0.0
    discount: Optional[float] = 0.0
    rack_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    distributor: Optional[str] = None
    distributor_id: Optional[UUID] = None

    @field_validator("expiry_date", mode="before")
    @classmethod
    def parse_expiry_date(cls, v: Any):
        if v is None or v == "" or (isinstance(v, str) and not v.strip()):
            return None
        return v

class InventoryItemCreate(InventoryItemBase):
    shop_id: UUID

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    manufacturer: Optional[str] = None
    batch_number: Optional[str] = None
    stock_quantity: Optional[int] = None
    loose_stock: Optional[int] = None
    pack_size: Optional[int] = None
    buying_price: Optional[float] = None
    hsn_code: Optional[str] = None
    unit_price: Optional[float] = None
    expiry_date: Optional[date] = None
    image_url: Optional[str] = None
    gst: Optional[float] = None
    discount: Optional[float] = None
    rack_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    distributor: Optional[str] = None
    distributor_id: Optional[UUID] = None

    @field_validator("expiry_date", mode="before")
    @classmethod
    def parse_expiry_date(cls, v: Any):
        if v is None or v == "" or (isinstance(v, str) and not v.strip()):
            return None
        return v

class InventoryItem(InventoryItemBase):
    id: UUID
    shop_id: UUID
    tenant_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
