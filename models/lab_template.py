import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID
from .database import Base

class LabTemplate(Base):
    __tablename__ = "lab_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    test_name = Column(String, default="")
    category = Column(String, default="General")
    type = Column(String, default="Standard")
    report_format = Column(String, default="PDF")
    is_active = Column(Boolean, default=True)
    description = Column(String, default="")
    show_patient_details = Column(Boolean, default=True)
    show_referrals = Column(Boolean, default=True)
    show_lab_logo = Column(Boolean, default=True)
    show_remarks_section = Column(Boolean, default=True)
    default_remarks = Column(String, default="")
    fields = Column(JSONB, default=list) # Array of TemplateField objects
    layout_config = Column(JSONB, default=dict) # ReportLayoutConfig object
