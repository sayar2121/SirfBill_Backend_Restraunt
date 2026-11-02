from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ShopSettingsBase(BaseModel):
    shop_id: Optional[UUID] = None
    shop_name: Optional[str] = None
    tagline: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    landline: Optional[str] = None
    email: Optional[str] = None
    gst_number: Optional[str] = None
    drug_licence: Optional[str] = None
    cin_number: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    ac_holder_name: Optional[str] = None
    account_holder_name: Optional[str] = None
    ac_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_id: Optional[str] = None
    terms_1: Optional[str] = None
    terms_2: Optional[str] = None
    terms_3: Optional[str] = None
    logo_url: Optional[str] = None
    qr_url: Optional[str] = None

class ShopSettingsUpdate(ShopSettingsBase):
    pass

class ShopSettingsOut(ShopSettingsBase):
    id: UUID
    
    class Config:
        from_attributes = True
