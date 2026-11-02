from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

class UserAddress(BaseModel):
    label: str
    street: str
    city: str
    state: str
    pincode: str
    phone: Optional[str] = None
    is_default: bool = False

class UserBase(BaseModel):
    tenant_id: Optional[UUID] = None  # Multi-tenancy
    outlet_id: Optional[UUID] = None  # Assigned restaurant outlet / branch
    branch_id: Optional[UUID] = None  # Alias for Flutter UI
    branch_name: Optional[str] = None # Resolved name of the branch
    role: str
    phone: str
    name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    saved_addresses: Optional[Any] = None
    is_active: Optional[bool] = True
    location: Optional[str] = None

class UserCreate(UserBase):
    model_config = ConfigDict(extra='allow')
    password: Optional[str] = None

class UserUpdate(BaseModel):
    model_config = ConfigDict(extra='allow')
    role: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    outlet_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    shop_id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None
    avatar_url: Optional[str] = None
    saved_addresses: Optional[Any] = None
    is_active: Optional[bool] = None
    location: Optional[str] = None

class User(UserBase):
    id: UUID
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
