import uuid
from sqlalchemy import Column, String, Float
import sqlalchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import UUID

from .database import Base

class LabCatalog(Base):
    __tablename__ = "lab_catalog"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    turnaround_time = Column(String)
    includes = Column(JSONB)
    test_code = Column(String, default="")
    description = Column(String, default="")
    category = Column(String, default="")
    template_id = Column(String, nullable=True)
    sample_type = Column(String, default="Blood")
    is_active = Column(sqlalchemy.Boolean, default=True)
    discounted_price = Column(Float, nullable=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)

