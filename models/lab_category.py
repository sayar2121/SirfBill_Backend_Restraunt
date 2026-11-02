import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy import UUID

from .database import Base

class LabCategory(Base):
    __tablename__ = "lab_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    description = Column(String, default="")
    is_active = Column(Boolean, default=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
