import strawberry
from typing import Optional
from uuid import UUID

from models.clinic_settings import ClinicSettings as ClinicSettingsModel
from models.database import get_db

@strawberry.type
class ClinicSettingsType:
    id: UUID
    primary_phone: str
    whatsapp_number: str
    email: str
    address: str
    support_hours: Optional[str]

@strawberry.type
class SettingsQuery:
    
    @strawberry.field
    def get_clinic_contact_details(self) -> Optional[ClinicSettingsType]:
        """
        Public/App Action: Fetches the clinic's dynamic contact information.
        """
        db = next(get_db())
        
        # Always fetch the first row
        db_settings = db.query(ClinicSettingsModel).first()
        
        return db_settings
