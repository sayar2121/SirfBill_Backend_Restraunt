import strawberry
from typing import Optional, Annotated
from uuid import UUID
from datetime import datetime, date
from strawberry.scalars import JSON

@strawberry.type
class LabBookingType:
    id: UUID
    user_id: UUID
    payment_method: str
    booked_items: JSON
    status: str
    total_amount: float
    preferred_date: date
    form_details: Optional[JSON]
    report_url: Optional[str]
    created_at: datetime
    
    # --- ADDED FOR ADMIN DISPATCH ---
    tenant_id: Optional[UUID]
    agent_id: Optional[UUID]
    admin_notes: Optional[str]
    # --------------------------------
    
    agent: Optional[Annotated["UserType", strawberry.lazy("graphql_api.types.user")]]
