from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class KitchenTicketItemResponse(BaseModel):
    id: UUID
    order_line_id: UUID
    item_name: str
    variant_name: str
    quantity: int
    modifiers_summary: Optional[str] = None
    special_instructions: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)

class KitchenTicketResponse(BaseModel):
    id: UUID
    order_id: UUID
    ticket_number: str
    station: str
    status: str
    server_user_id: Optional[UUID] = None
    notes: Optional[str] = None
    is_reprint: bool
    reprint_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    kot_pdf_url: Optional[str] = None
    items: List[KitchenTicketItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

class KitchenEventCreate(BaseModel):
    to_status: str # PREPARING, READY, SERVED, CANCELLED
    notes: Optional[str] = None

class KitchenEventResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    actor_id: Optional[UUID] = None
    from_status: Optional[str] = None
    to_status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KitchenItemStatusUpdate(BaseModel):
    status: str # PENDING, PREPARING, READY, SERVED, CANCELLED

class CancelKitchenTicket(BaseModel):
    reason: str = Field(..., min_length=3)

