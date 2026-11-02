from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from .print_service import PrintServiceOut

class PrintJobBase(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    service_id: Optional[UUID] = None
    file_name: Optional[str] = None
    pages: Optional[int] = 1
    copies: Optional[int] = 1
    color_type: Optional[str] = None
    status: Optional[str] = "PENDING"
    total_amount: Optional[float] = 0.0

class PrintJobCreate(PrintJobBase):
    shop_id: UUID

class PrintJobUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    service_id: Optional[UUID] = None
    file_name: Optional[str] = None
    pages: Optional[int] = None
    copies: Optional[int] = None
    color_type: Optional[str] = None
    status: Optional[str] = None
    total_amount: Optional[float] = None

class PrintJobOut(PrintJobBase):
    id: UUID
    shop_id: UUID
    created_at: datetime
    updated_at: datetime
    service: Optional[PrintServiceOut] = None

    model_config = ConfigDict(from_attributes=True)
