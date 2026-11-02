from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class LabCategoryBase(BaseModel):
    name: str
    description: Optional[str] = ""
    is_active: Optional[bool] = True

class LabCategoryCreate(LabCategoryBase):
    pass

class LabCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class LabCategoryResponse(LabCategoryBase):
    id: UUID
    tenant_id: Optional[UUID] = None

    class Config:
        from_attributes = True
