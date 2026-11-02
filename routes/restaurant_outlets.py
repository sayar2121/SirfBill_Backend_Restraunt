import os
import shutil
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import User
from models.restaurant_outlet import RestaurantOutlet
from schemas.restaurant_outlet import RestaurantOutletCreate, RestaurantOutletUpdate, RestaurantOutletResponse
from dependencies import get_current_user, get_restaurant_manager, get_optional_restaurant_staff

router = APIRouter(
    prefix="/api/restaurant/outlets",
    tags=["Restaurant - Outlets"]
)

@router.get("", response_model=List[RestaurantOutletResponse])
def get_outlets(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    """
    List all restaurant outlets accessible by the current tenant/user.
    Allows POS/counter sessions without hard failure.
    """
    query = db.query(RestaurantOutlet)
    if current_user and current_user.tenant_id:
        query = query.filter(RestaurantOutlet.tenant_id == current_user.tenant_id)
    return query.all()

@router.post("", response_model=RestaurantOutletResponse, status_code=status.HTTP_201_CREATED)
def create_outlet(
    payload: RestaurantOutletCreate,
    db: Session = Depends(get_db),
    manager_user: User = Depends(get_restaurant_manager)
):
    """
    Create a new restaurant outlet (Manager/Admin/Owner only).
    """
    tenant_id = manager_user.tenant_id or payload.tenant_id
    db_outlet = RestaurantOutlet(
        tenant_id=tenant_id,
        shop_id=payload.shop_id,
        name=payload.name,
        code=payload.code,
        timezone=payload.timezone,
        currency=payload.currency,
        service_settings=payload.service_settings or {
            "dine_in_enabled": True,
            "takeaway_enabled": True,
            "delivery_enabled": True
        },
        is_active=payload.is_active
    )
    db.add(db_outlet)
    db.commit()
    db.refresh(db_outlet)
    return db_outlet

@router.get("/{outlet_id}", response_model=RestaurantOutletResponse)
def get_outlet_by_id(
    outlet_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    query = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == outlet_id)
    if current_user and current_user.tenant_id:
        query = query.filter(RestaurantOutlet.tenant_id == current_user.tenant_id)
    outlet = query.first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Restaurant outlet not found")
    return outlet

@router.patch("/{outlet_id}", response_model=RestaurantOutletResponse)
def update_outlet(
    outlet_id: UUID,
    payload: RestaurantOutletUpdate,
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    query = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == outlet_id)
    if manager_user and manager_user.tenant_id:
        query = query.filter(RestaurantOutlet.tenant_id == manager_user.tenant_id)
    outlet = query.first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Restaurant outlet not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(outlet, field, value)

    db.commit()
    db.refresh(outlet)
    return outlet


@router.delete("/{outlet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_outlet(
    outlet_id: UUID,
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    """
    Delete a restaurant outlet and cascade delete all its credentials,
    menus, categories, tables, orders, and linked records.
    """
    from routes.shop_admin import cascade_delete_outlet_and_data
    cascade_delete_outlet_and_data(outlet_id, db)
    db.commit()
    return None


@router.post("/{outlet_id}/logo")
async def upload_outlet_logo(
    outlet_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    """
    Upload and store the logo for a specific restaurant outlet.
    """
    outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Restaurant outlet not found")

    os.makedirs("uploads/outlets", exist_ok=True)
    filename = f"logo_{outlet_id.hex[:8]}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join("uploads", "outlets", filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logo_url = f"/{file_path}"
    outlet.logo_url = logo_url

    # Also sync into service_settings dict for backwards compatibility
    svc = dict(outlet.service_settings or {})
    svc["logo_url"] = logo_url
    outlet.service_settings = svc

    db.commit()
    db.refresh(outlet)
    return {"message": "Logo uploaded successfully", "logo_url": logo_url}


from models.shop_settings import ShopSettings

@router.get("/{outlet_id}/billing-settings")
def get_outlet_billing_settings(
    outlet_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    """
    Returns GST rates, service charges, round-off rules, invoice prefixes, and UPI details for POS billing.
    """
    outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Restaurant outlet not found")

    shop_settings = None
    if outlet.shop_id:
        shop_settings = db.query(ShopSettings).filter(ShopSettings.shop_id == outlet.shop_id).first()
    if not shop_settings:
        shop_settings = db.query(ShopSettings).first()

    svc = outlet.service_settings or {}
    logo_url = outlet.logo_url or svc.get("logo_url") or (shop_settings.logo_url if shop_settings else None)
    upi_id = outlet.upi_id or svc.get("upi_id") or (shop_settings.upi_id if shop_settings else None)

    return {
        "outlet_id": str(outlet.id),
        "outlet_name": outlet.name,
        "logo_url": logo_url,
        "currency": outlet.currency,
        "gst_rates": {
            "default_tax_rate": 5.0,
            "cgst_rate": 2.5,
            "sgst_rate": 2.5,
            "gst_number": (shop_settings.gst_number if shop_settings else None) or svc.get("gst_number", "")
        },
        "service_charge_percent": float(svc.get("service_charge_percent", 0.0)),
        "packaging_charge": float(svc.get("packaging_charge", 0.0)),
        "round_off_rule": "NEAREST_RUPEE",
        "invoice_prefix": svc.get("invoice_prefix", "ORD-"),
        "upi_id": upi_id,
        "bank_details": {
            "bank_name": outlet.bank_name or (shop_settings.bank_name if shop_settings else None) or svc.get("bank_name"),
            "bank_account_no": outlet.bank_account_no or (shop_settings.ac_number if shop_settings else None) or svc.get("bank_account_no"),
            "bank_ifsc": outlet.bank_ifsc or (shop_settings.ifsc_code if shop_settings else None) or svc.get("bank_ifsc"),
            "bank_branch": outlet.bank_branch or (shop_settings.branch_name if shop_settings else None) or svc.get("bank_branch"),
            "bank_account_name": outlet.bank_account_name or (shop_settings.ac_holder_name if shop_settings else None) or svc.get("bank_account_name")
        },
        "dine_in_enabled": svc.get("dine_in_enabled", True),
        "takeaway_enabled": svc.get("takeaway_enabled", True),
        "delivery_enabled": svc.get("delivery_enabled", True)
    }
