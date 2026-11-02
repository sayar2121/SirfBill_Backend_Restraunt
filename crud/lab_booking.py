from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException

from models.lab_booking import LabBooking
from models.lab_catalog import LabCatalog
from models.enums import BookingStatus
from schemas.lab_booking import LabBookingCreate, LabBookingUpdate

def get_lab_booking(db: Session, booking_id: UUID) -> Optional[LabBooking]:
    return db.query(LabBooking).filter(LabBooking.id == booking_id).first()

def get_lab_bookings_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[LabBooking]:
    return db.query(LabBooking).filter(LabBooking.user_id == user_id).offset(skip).limit(limit).all()

def get_lab_bookings(db: Session, skip: int = 0, limit: int = 100) -> List[LabBooking]:
    return db.query(LabBooking).offset(skip).limit(limit).all()

def create_lab_booking(db: Session, booking: LabBookingCreate, context_tenant_id: Optional[UUID] = None) -> LabBooking:
    # 1. Fetch the lab items from catalog based on item_ids
    items = db.query(LabCatalog).filter(LabCatalog.id.in_(booking.item_ids)).all()
    
    if len(items) != len(booking.item_ids):
        # Some items were not found or duplicate IDs were passed
        raise HTTPException(status_code=400, detail="One or more items in the cart are invalid")
        
    # 2. Calculate total amount
    total_amount = sum(item.price for item in items)
    
    # 3. Create the JSONB payload for booked_items
    booked_items_json = [
        {"id": str(item.id), "title": item.title, "type": item.type, "price": item.price}
        for item in items
    ]
    
    # 4. Save to DB
    tenant_id_to_use = context_tenant_id if context_tenant_id else booking.tenant_id
    db_booking = LabBooking(
        tenant_id=tenant_id_to_use,
        user_id=booking.user_id,
        payment_method=booking.payment_method,
        status=BookingStatus.PENDING_CONFIRMATION,
        total_amount=total_amount,
        preferred_date=booking.preferred_date,
        form_details=booking.form_details,
        booked_items=booked_items_json
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def update_lab_booking(db: Session, db_booking: LabBooking, booking_update: LabBookingUpdate) -> LabBooking:
    update_data = booking_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_booking, key, value)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def delete_lab_booking(db: Session, db_booking: LabBooking) -> LabBooking:
    db.delete(db_booking)
    db.commit()
    return db_booking

def assign_agent_to_booking(
    db: Session, 
    booking_id: UUID, 
    agent_id: UUID, 
    admin_notes: Optional[str] = None
) -> Optional[LabBooking]:
    db_booking = get_lab_booking(db, booking_id)
    if not db_booking:
        return None
        
    db_booking.agent_id = agent_id
    db_booking.status = BookingStatus.AGENT_ASSIGNED
    
    if admin_notes:
        db_booking.admin_notes = admin_notes
        
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_admin_lab_bookings(
    db: Session, 
    tenant_id: Optional[UUID] = None, 
    status: Optional[BookingStatus] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[LabBooking]:
    """Admin dashboard query with dynamic filtering."""
    query = db.query(LabBooking)
    
    # Filter by tenant if applicable
    if tenant_id:
        query = query.filter(LabBooking.tenant_id == tenant_id)
        
    # Filter by status (e.g., viewing only PENDING_CONFIRMATION)
    if status:
        query = query.filter(LabBooking.status == status)
        
    return query.order_by(LabBooking.created_at.desc()).offset(skip).limit(limit).all()
