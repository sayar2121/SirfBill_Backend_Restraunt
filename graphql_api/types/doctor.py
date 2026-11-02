import strawberry
from typing import Optional
from uuid import UUID
from datetime import datetime

@strawberry.type
class DoctorType:
    id: UUID
    name: str
    specialty_key: str
    experience: Optional[str]
    fee: float
    image_url: Optional[str]
    about: Optional[str]
    created_at: datetime
