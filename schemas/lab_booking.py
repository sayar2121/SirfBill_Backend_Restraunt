from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, List
from uuid import UUID
from datetime import datetime, date
from models.enums import BookingStatus

class LabBookingCreate(BaseModel):
    tenant_id: Optional[UUID] = None
    user_id: UUID
    item_ids: List[UUID]  # Frontend sends a list of cart item IDs!
    payment_method: str = "COD" # Can be "COD" or "ONLINE"
    preferred_date: date
    form_details: Optional[Any] = None

class LabBookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None
    payment_method: Optional[str] = None
    report_url: Optional[str] = None
    agent_id: Optional[UUID] = None  # ADDED: To assign lab tech
    admin_notes: Optional[str] = None # ADDED: Internal use only

class LabBooking(BaseModel):
    id: UUID
    tenant_id: Optional[UUID] = None
    user_id: UUID
    payment_method: str
    booked_items: Any
    status: BookingStatus
    total_amount: float
    preferred_date: date
    form_details: Optional[Any] = None
    report_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
