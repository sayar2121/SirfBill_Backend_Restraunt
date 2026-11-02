from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
import os
import aiofiles

from schemas.lab_booking import LabBookingCreate, LabBookingUpdate, LabBooking as LabBookingSchema
from crud import lab_booking as crud_lab_booking
from models.lab_catalog import LabCatalog as LabCatalogModel
from models.lab_booking import LabBooking as LabBookingModel
from models.database import get_db

# 🛡️ IMPORT YOUR SECURITY DEPENDENCIES
from dependencies import get_current_user, get_admin_user
from models.user import User

router = APIRouter(
    prefix="/api",
    tags=["Lab Bookings"]
)

def notify_patient_report_ready(booking_id: UUID, user_id: UUID):
    # Logic to push an FCM notification or APITXT SMS to the user
    pass

# ==========================================
# 📱 CUSTOMER APP ROUTES
# ==========================================

@router.get("/lab-bookings", response_model=list[LabBookingSchema])
def get_user_lab_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient Action: Fetch all lab bookings for the logged-in user.
    """
    return crud_lab_booking.get_lab_bookings_by_user(db=db, user_id=current_user.id)

@router.post("/lab-bookings", response_model=LabBookingSchema, status_code=status.HTTP_201_CREATED)

def create_lab_booking(
    booking: LabBookingCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 🛡️ Must be logged in!
):
    """
    Patient Action: Submit a cart of lab tests.
    """
    items = db.query(LabCatalogModel).filter(LabCatalogModel.id.in_(booking.item_ids)).all()
    if not items:
        raise HTTPException(status_code=400, detail="No valid items found in cart.")

    total_amount = sum(item.price for item in items)
    
    booked_items_snapshot = [
        {"id": str(item.id), "title": item.title, "price": item.price, "type": item.type}
        for item in items
    ]

    new_booking = LabBookingModel(
        user_id=booking.user_id,
        payment_method=booking.payment_method,
        booked_items=booked_items_snapshot,
        status="PENDING_CONFIRMATION",
        total_amount=total_amount,
        preferred_date=booking.preferred_date,
        form_details=booking.form_details
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking




@router.patch("/lab-bookings/{booking_id}/cancel", response_model=LabBookingSchema)
def cancel_lab_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient Action: Cancel a lab booking.
    """
    db_booking = crud_lab_booking.get_lab_booking(db, booking_id=booking_id)
    if not db_booking:
        raise HTTPException(status_code=404, detail="Lab booking not found")
    
    if str(db_booking.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")

    booking_update = LabBookingUpdate(status="CANCELLED")
    return crud_lab_booking.update_lab_booking(db=db, db_booking=db_booking, booking_update=booking_update)


@router.get("/lab-bookings/{booking_id}/receipt")
def download_lab_receipt(
    booking_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Patient Action: Download a PDF receipt for the lab booking.
    """
    from fastapi.responses import Response
    from utils.pdf_generator import generate_lab_receipt_pdf
    
    db_booking = crud_lab_booking.get_lab_booking(db, booking_id=booking_id)
    if not db_booking:
        raise HTTPException(status_code=404, detail="Lab booking not found")
        
    # Optional authorization check
    # if str(db_booking.user_id) != str(current_user.id):
    #     raise HTTPException(status_code=403, detail="Not authorized to view this receipt")
        
    pdf_buffer = generate_lab_receipt_pdf(db_booking)
    
    headers = {
        "Content-Disposition": f'attachment; filename="receipt_{booking_id}.pdf"'
    }
    
    return Response(content=pdf_buffer.getvalue(), media_type="application/pdf", headers=headers)

# ==========================================
# 💻 ADMIN PANEL ROUTES (Highly Secured)

# ==========================================

@router.post("/admin/lab-bookings/{booking_id}/upload-report", response_model=LabBookingSchema)
async def upload_lab_report(
    booking_id: UUID, 
    file: UploadFile = File(...), 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED: Only Admins can do this!
):
    """
    Admin Action: Upload a PDF lab report once the results are ready.
    """
    db_booking = crud_lab_booking.get_lab_booking(db, booking_id=booking_id)
    if not db_booking:
        raise HTTPException(status_code=404, detail="Lab booking not found")

    if not file.filename.endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Invalid file format.")

    upload_dir = "./uploads/reports"
    os.makedirs(upload_dir, exist_ok=True)

    file_extension = file.filename.split(".")[-1]
    file_path = f"{upload_dir}/lab_{booking_id}.{file_extension}"
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    public_url = f"/uploads/reports/lab_{booking_id}.{file_extension}"
    
    booking_update = LabBookingUpdate(
        report_url=public_url,
        status="REPORT_READY"
    )
    
    updated_booking = crud_lab_booking.update_lab_booking(db=db, db_booking=db_booking, booking_update=booking_update)
    
    # Dispatch the notification instantly
    background_tasks.add_task(notify_patient_report_ready, booking_id, updated_booking.user_id)
    
    return updated_booking

@router.patch("/admin/lab-bookings/{booking_id}", response_model=LabBookingSchema)
def update_lab_booking_status(
    booking_id: UUID, 
    booking_update: LabBookingUpdate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin Action: Update the status manually (e.g., PENDING -> SAMPLE_COLLECTED).
    """
    db_booking = crud_lab_booking.get_lab_booking(db, booking_id=booking_id)
    if not db_booking:
        raise HTTPException(status_code=404, detail="Lab booking not found")
    
    return crud_lab_booking.update_lab_booking(db=db, db_booking=db_booking, booking_update=booking_update)
