import strawberry
from typing import Optional, Annotated
from uuid import UUID
from datetime import datetime, date
from strawberry.scalars import JSON

@strawberry.type
class AppointmentType:
    id: UUID
    user_id: UUID
    doctor_id: UUID
    status: str
    preferred_date: date
    form_details: Optional[JSON]
    prescription_url: Optional[str]
    created_at: datetime
    
    tenant_id: Optional[UUID]
    agent_id: Optional[UUID]
    admin_notes: Optional[str]
    
    doctor: Annotated["DoctorType", strawberry.lazy("graphql_api.types.doctor")]
    agent: Optional[Annotated["UserType", strawberry.lazy("graphql_api.types.user")]]
    shop_bill: Optional[Annotated["ShopBillType", strawberry.lazy("graphql_api.types.shop")]]
