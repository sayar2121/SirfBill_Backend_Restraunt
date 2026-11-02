from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# Outlets
class RestaurantOutletBase(BaseModel):
    name: str = Field(..., max_length=150)
    code: Optional[str] = Field(None, max_length=50)
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"
    service_settings: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = None
    upi_id: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_branch: Optional[str] = None
    bank_account_name: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(extra="allow", from_attributes=True)

class RestaurantOutletCreate(RestaurantOutletBase):
    tenant_id: UUID
    shop_id: Optional[UUID] = None

class RestaurantOutletUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    service_settings: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = None
    upi_id: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_branch: Optional[str] = None
    bank_account_name: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="allow")

class RestaurantOutletResponse(RestaurantOutletBase):
    id: UUID
    tenant_id: UUID
    shop_id: Optional[UUID] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    outlet_type: Optional[str] = None
    gstin: Optional[str] = None
    fssai: Optional[str] = None
    invoice_prefix: Optional[str] = None
    tax_rate: Optional[float] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    weekly_closing: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    upi_id: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_branch: Optional[str] = None
    bank_account_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="allow", from_attributes=True)
