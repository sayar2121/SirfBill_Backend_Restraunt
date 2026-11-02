from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from models.database import Base

class ClinicSettings(Base):
    """
    Stores global configuration for the app (like contact numbers).
    We will only ever keep ONE row in this table.
    """
    __tablename__ = "clinic_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primary_phone = Column(String, nullable=False)
    whatsapp_number = Column(String, nullable=False)
    email = Column(String, nullable=False)
    address = Column(String, nullable=False)
    support_hours = Column(String, nullable=True)
