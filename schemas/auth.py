from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class SendOTPRequest(BaseModel):
    tenant_id: Optional[UUID] = None
    phone: str
    channel: str = "sms" # "sms" or "whatsapp"

class VerifyOTPRequest(BaseModel):
    tenant_id: Optional[UUID] = None
    phone: str
    otp: str
    name: str = "New User" # In case they are registering for the first time

class AdminLoginRequest(BaseModel):
    tenant_id: Optional[UUID] = None
    email: str
    password: str
