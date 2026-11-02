from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
import os
import aiofiles

from schemas.user import UserCreate, UserUpdate, User as UserSchema, UserAddress
from crud import user as crud_user
from models.database import get_db

from typing import List, Optional

router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)

admin_router = APIRouter(
    prefix="/api/admin/users",
    tags=["Admin - Users"]
)

@router.get("", response_model=List[UserSchema])
@admin_router.get("", response_model=List[UserSchema])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    role: Optional[str] = None,
    tenant_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Fetch all users or filter by role (e.g. CASHIER, KITCHEN, MANAGER, USER) and search term.
    Resolves branch_id and branch_name for each staff user.
    """
    from models.user import User
    from models.restaurant_outlet import RestaurantOutlet

    query = db.query(User)
    
    if role:
        query = query.filter(User.role.ilike(role))
    
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
        
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | 
            (User.phone.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
        
    users = query.offset(skip).limit(limit).all()
    outlets = {o.id: o.name for o in db.query(RestaurantOutlet).all()}

    results = []
    for u in users:
        u_schema = UserSchema.model_validate(u)
        if u.outlet_id and u.outlet_id in outlets:
            u_schema.branch_id = u.outlet_id
            u_schema.branch_name = outlets[u.outlet_id]
        results.append(u_schema)
    return results


@router.post("", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
@router.post("/create", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
@admin_router.post("", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
@admin_router.post("/create", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    from models.user import User
    from models.restaurant_outlet import RestaurantOutlet

    target_branch = user.outlet_id or user.branch_id or getattr(user, 'shop_id', None)

    # 1. If email/username provided, check or update existing
    if user.email:
        existing = db.query(User).filter(User.email == user.email).first()
        if existing:
            if user.password:
                existing.password = user.password
            existing.role = user.role.upper()
            existing.name = user.name
            if target_branch:
                existing.outlet_id = target_branch
            db.commit()
            db.refresh(existing)
            resp = UserSchema.model_validate(existing)
            if existing.outlet_id:
                outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == existing.outlet_id).first()
                if outlet:
                    resp.branch_id = outlet.id
                    resp.branch_name = outlet.name
            return resp

    # 2. Check if a user with this phone number already exists (only for USER role)
    if user.phone and user.role.upper() == "USER":
        db_user = crud_user.get_user_by_phone(db, phone=user.phone, tenant_id=user.tenant_id)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with phone {user.phone} already exists ({db_user.name}). Please use the search bar."
            )
        
    from datetime import datetime
    user_dict = user.model_dump()
    allowed_cols = {"id", "tenant_id", "outlet_id", "role", "phone", "name", "email", "password", "avatar_url", "saved_addresses", "is_active", "location", "created_at"}
    filtered_kwargs = {k: v for k, v in user_dict.items() if k in allowed_cols}
    filtered_kwargs["role"] = user.role.upper()
    if target_branch and "outlet_id" not in filtered_kwargs:
        filtered_kwargs["outlet_id"] = target_branch
    if not filtered_kwargs.get("created_at"):
        filtered_kwargs["created_at"] = datetime.utcnow()
    new_user = User(**filtered_kwargs)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    resp = UserSchema.model_validate(new_user)
    if new_user.outlet_id:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == new_user.outlet_id).first()
        if outlet:
            resp.branch_id = outlet.id
            resp.branch_name = outlet.name
    return resp

@router.get("/{user_id}", response_model=UserSchema)
@admin_router.get("/{user_id}", response_model=UserSchema)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    from models.restaurant_outlet import RestaurantOutlet
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    resp = UserSchema.model_validate(db_user)
    if db_user.outlet_id:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == db_user.outlet_id).first()
        if outlet:
            resp.branch_id = outlet.id
            resp.branch_name = outlet.name
    return resp

@router.patch("/{user_id}", response_model=UserSchema)
@router.put("/{user_id}", response_model=UserSchema)
@admin_router.patch("/{user_id}", response_model=UserSchema)
@admin_router.put("/{user_id}", response_model=UserSchema)
def update_user(user_id: UUID, user_update: UserUpdate, db: Session = Depends(get_db)):
    from models.restaurant_outlet import RestaurantOutlet

    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    # Check if phone is being updated and if it's already taken
    if user_update.phone and user_update.phone != db_user.phone:
        existing_phone = crud_user.get_user_by_phone(db, phone=user_update.phone, tenant_id=db_user.tenant_id)
        if existing_phone and existing_phone.id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Phone number already in use"
            )

    updated_u = crud_user.update_user(db=db, db_user=db_user, user_update=user_update)
    resp = UserSchema.model_validate(updated_u)
    if updated_u.outlet_id:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == updated_u.outlet_id).first()
        if outlet:
            resp.branch_id = outlet.id
            resp.branch_name = outlet.name
    return resp

@router.post("/{user_id}/upload-avatar", response_model=UserSchema)
async def upload_user_avatar(
    user_id: UUID, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    """
    Patient Action: Upload a profile picture.
    Saves locally and updates the user's avatar_url.
    """
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    upload_dir = "./uploads/profiles"
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = file.filename or "avatar.jpg"
    if "." in filename:
        file_extension = filename.split(".")[-1].lower()
    else:
        file_extension = "jpg"
        
    file_path = f"{upload_dir}/user_{user_id}.{file_extension}"
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    import time
    public_url = f"/uploads/profiles/user_{user_id}.{file_extension}?v={int(time.time())}"
    
    user_update = UserUpdate(avatar_url=public_url)
    return crud_user.update_user(db=db, db_user=db_user, user_update=user_update)


@router.get("/{user_id}/upcoming-appointment")
def get_upcoming_appointment(user_id: UUID, db: Session = Depends(get_db)):
    """
    Legacy medical endpoint: returns None in restaurant backend.
    """
    return None

@router.get("/{user_id}/appointments")
def get_user_appointments(user_id: UUID, db: Session = Depends(get_db)):
    """
    Legacy medical endpoint: returns empty list in restaurant backend.
    """
    return []

import uuid

@router.post("/{user_id}/address", response_model=UserSchema)
def add_user_address(
    user_id: UUID,
    address: UserAddress,
    db: Session = Depends(get_db)
):
    """
    Patient Action: Add a new delivery address.
    """
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    addresses = db_user.saved_addresses
    if not isinstance(addresses, list):
        addresses = []
        
    addr_dict = address.model_dump()
    addr_dict["id"] = str(uuid.uuid4())
    
    if addr_dict.get("is_default"):
        for a in addresses:
            a["is_default"] = False
            
    addresses.append(addr_dict)
    
    from sqlalchemy.orm.attributes import flag_modified
    db_user.saved_addresses = addresses
    flag_modified(db_user, "saved_addresses")
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}/address/{address_id}", response_model=UserSchema)
def update_user_address(
    user_id: UUID,
    address_id: str,
    address: UserAddress,
    db: Session = Depends(get_db)
):
    """
    Patient Action: Update a delivery address.
    """
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    addresses = db_user.saved_addresses
    if not isinstance(addresses, list):
        addresses = []
        
    found = False
    for a in addresses:
        if a.get("id") == address_id:
            addr_dict = address.model_dump()
            addr_dict["id"] = address_id
            if addr_dict.get("is_default"):
                for other in addresses:
                    other["is_default"] = False
            a.update(addr_dict)
            found = True
            break
            
    if not found:
        raise HTTPException(status_code=404, detail="Address not found")
        
    from sqlalchemy.orm.attributes import flag_modified
    db_user.saved_addresses = addresses
    flag_modified(db_user, "saved_addresses")
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}/address/{address_id}", response_model=UserSchema)
def delete_user_address(
    user_id: UUID,
    address_id: str,
    db: Session = Depends(get_db)
):
    """
    Patient Action: Delete a delivery address.
    """
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    addresses = db_user.saved_addresses
    if not isinstance(addresses, list):
        addresses = []
        
    initial_len = len(addresses)
    addresses = [a for a in addresses if a.get("id") != address_id]
    
    if len(addresses) == initial_len:
        raise HTTPException(status_code=404, detail="Address not found")
        
    from sqlalchemy.orm.attributes import flag_modified
    db_user.saved_addresses = addresses
    flag_modified(db_user, "saved_addresses")
    db.commit()
    db.refresh(db_user)
    return db_user

from sqlalchemy.exc import IntegrityError
@router.delete("/{user_id}")
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    try:
        db.delete(db_user)
        db.commit()
        return {"message": "User deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete customer because they have bills or appointments attached. Please mark them as Inactive instead."
        )
