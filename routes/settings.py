from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from models.database import get_db
from dependencies import get_admin_user
from models.user import User
from models.clinic_settings import ClinicSettings

router = APIRouter(
    prefix="/api/admin/settings",
    tags=["Admin - Settings"]
)

class ClinicSettingsUpdate(BaseModel):
    primary_phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    support_hours: Optional[str] = None

@router.patch("/", status_code=status.HTTP_200_OK)
def update_clinic_settings(
    settings_update: ClinicSettingsUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED: Admin Only!
):
    """
    Admin Action: Updates the global contact details for the clinic.
    """
    # Grab the very first row in the settings table (there should only be one)
    db_settings = db.query(ClinicSettings).first()
    
    if not db_settings:
        # If it doesn't exist for some reason, create it
        db_settings = ClinicSettings(
            primary_phone=settings_update.primary_phone or "",
            whatsapp_number=settings_update.whatsapp_number or "",
            email=settings_update.email or "",
            address=settings_update.address or "",
            support_hours=settings_update.support_hours or ""
        )
        db.add(db_settings)
    else:
        # Update existing row
        if settings_update.primary_phone is not None:
            db_settings.primary_phone = settings_update.primary_phone
        if settings_update.whatsapp_number is not None:
            db_settings.whatsapp_number = settings_update.whatsapp_number
        if settings_update.email is not None:
            db_settings.email = settings_update.email
        if settings_update.address is not None:
            db_settings.address = settings_update.address
        if settings_update.support_hours is not None:
            db_settings.support_hours = settings_update.support_hours
            
    db.commit()
    db.refresh(db_settings)
    
    return db_settings
