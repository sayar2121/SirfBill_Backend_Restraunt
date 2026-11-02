import strawberry
from typing import Optional
from uuid import UUID
from strawberry.scalars import JSON

@strawberry.type
class LabCatalogType:
    id: UUID
    type: str
    title: str
    price: float
    turnaround_time: Optional[str]
    includes: Optional[JSON]
