from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from uuid import UUID

class LabCatalogBase(BaseModel):
    tenant_id: Optional[UUID] = None
    type: str
    title: str
    price: float
    turnaround_time: Optional[str] = None
    includes: Optional[Any] = None
    test_code: Optional[str] = ""
    description: Optional[str] = ""
    category: Optional[str] = ""
    template_id: Optional[str] = None
    sample_type: Optional[str] = "Blood"
    is_active: Optional[bool] = True
    discounted_price: Optional[float] = None

class LabCatalogCreate(LabCatalogBase):
    pass

class LabCatalogUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    price: Optional[float] = None
    turnaround_time: Optional[str] = None
    includes: Optional[Any] = None
    test_code: Optional[str] = ""
    description: Optional[str] = ""
    category: Optional[str] = ""
    template_id: Optional[str] = None
    sample_type: Optional[str] = "Blood"
    is_active: Optional[bool] = True
    discounted_price: Optional[float] = None

class LabCatalog(LabCatalogBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
