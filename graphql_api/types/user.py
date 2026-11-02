import strawberry
from typing import Optional, Annotated, List
from uuid import UUID
from datetime import datetime
from strawberry.scalars import JSON

@strawberry.type
class UserType:
    id: UUID
    role: str
    phone: str
    name: str
    avatar_url: Optional[str]
    saved_addresses: Optional[JSON]
    created_at: datetime
    
    appointments: List[Annotated["AppointmentType", strawberry.lazy("graphql_api.types.appointment")]]
    lab_bookings: List[Annotated["LabBookingType", strawberry.lazy("graphql_api.types.lab_booking")]]
