from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class ShopCreate(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: str
    code: Optional[str] = None
    address: str
    city: Optional[str] = None
    contact_number: Optional[str] = None
    status: Optional[str] = "Active"
    is_primary: Optional[bool] = False
    account_holder_name: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class ShopUpdate(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    contact_number: Optional[str] = None
    status: Optional[str] = None
    is_primary: Optional[bool] = None
    account_holder_name: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class ShopResponse(BaseModel):
    id: UUID
    tenant_id: Optional[UUID] = None
    name: str
    code: Optional[str] = None
    address: str
    city: Optional[str] = None
    contact_number: Optional[str] = None
    status: str
    is_primary: bool
    account_holder_name: Optional[str] = None
    created_at: datetime
    extra_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
