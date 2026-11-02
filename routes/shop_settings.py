from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from models import ShopSettings
from schemas.shop_settings import ShopSettingsOut, ShopSettingsUpdate
from dependencies import get_db
import shutil
import os

router = APIRouter(prefix="/api/admin/shop-settings", tags=["Shop Settings"])

@router.get("/", response_model=ShopSettingsOut)
def get_settings(shop_id: Optional[str] = Query(None), tenant_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    sid = shop_id or tenant_id
    if sid:
        settings = db.query(ShopSettings).filter(ShopSettings.shop_id == sid).first()
    else:
        settings = db.query(ShopSettings).first()
        
    if not settings:
        settings = ShopSettings(shop_id=sid if sid else None)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    if not settings.cin_number and settings.drug_licence:
        settings.cin_number = settings.drug_licence
    elif not settings.drug_licence and settings.cin_number:
        settings.drug_licence = settings.cin_number

    # Sync ac_holder_name with account_holder_name
    if getattr(settings, 'ac_holder_name', None):
        setattr(settings, 'account_holder_name', settings.ac_holder_name)

    return settings

@router.put("/", response_model=ShopSettingsOut)
def update_settings(data: ShopSettingsUpdate, shop_id: Optional[str] = Query(None), tenant_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    sid = data.shop_id or shop_id or tenant_id
    if sid:
        settings = db.query(ShopSettings).filter(ShopSettings.shop_id == sid).first()
    else:
        settings = db.query(ShopSettings).first()
        
    if not settings:
        settings = ShopSettings(shop_id=sid if sid else None)
        db.add(settings)
        
    for key, value in data.dict(exclude_unset=True).items():
        setattr(settings, key, value)

    # Sync cin_number and drug_licence so printing bills work with both fields
    if data.cin_number is not None:
        settings.drug_licence = data.cin_number
    elif data.drug_licence is not None:
        settings.cin_number = data.drug_licence

    # Support both account_holder_name and ac_holder_name updates
    if data.account_holder_name is not None:
        settings.ac_holder_name = data.account_holder_name
    elif data.ac_holder_name is not None:
        settings.ac_holder_name = data.ac_holder_name
        
    db.commit()
    db.refresh(settings)
    if getattr(settings, 'ac_holder_name', None):
        setattr(settings, 'account_holder_name', settings.ac_holder_name)
    return settings

@router.post("/upload/logo")
async def upload_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs("uploads/shop", exist_ok=True)
    file_path = f"uploads/shop/logo_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    settings = db.query(ShopSettings).first()
    if not settings:
        settings = ShopSettings()
        db.add(settings)
    
    settings.logo_url = f"/{file_path}"
    db.commit()
    return {"url": settings.logo_url}

@router.post("/upload/qr")
async def upload_qr(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs("uploads/shop", exist_ok=True)
    file_path = f"uploads/shop/qr_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    settings = db.query(ShopSettings).first()
    if not settings:
        settings = ShopSettings()
        db.add(settings)
    
    settings.qr_url = f"/{file_path}"
    db.commit()
    return {"url": settings.qr_url}
