from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
import os
import aiofiles

from fastapi.responses import StreamingResponse
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from schemas.appointment import AppointmentCreate, AppointmentUpdate, Appointment as AppointmentSchema
from crud import appointment as crud_appointment
from models.database import get_db

from dependencies import get_current_user, get_admin_user
from models.user import User

router = APIRouter(
    prefix="/api",
    tags=["Appointments"]
)

@router.post("/appointments", response_model=AppointmentSchema, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment: AppointmentCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient Action: Submit a lead-generation inquiry form for a clinic visit.
    The status will default to "pending".
    """
    return crud_appointment.create_appointment(db=db, appointment=appointment)

@router.patch("/appointments/{appointment_id}/cancel", response_model=AppointmentSchema)
def cancel_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient Action: Cancel an appointment.
    """
    db_appointment = crud_appointment.get_appointment(db, appointment_id=appointment_id)
    if not db_appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Appointment not found"
        )
        
    if str(db_appointment.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
        
    appointment_update = AppointmentUpdate(status="CANCELLED")
    return crud_appointment.update_appointment(db=db, db_appointment=db_appointment, appointment_update=appointment_update)

@router.patch("/admin/appointments/{appointment_id}", response_model=AppointmentSchema)
def update_appointment(
    appointment_id: UUID, 
    appointment_update: AppointmentUpdate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: Update the status of an appointment (e.g., PENDING -> CONFIRMED).
    """
    db_appointment = crud_appointment.get_appointment(db, appointment_id=appointment_id)
    if not db_appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Appointment not found"
        )
    
    return crud_appointment.update_appointment(db=db, db_appointment=db_appointment, appointment_update=appointment_update)

@router.post("/admin/appointments/{appointment_id}/upload-prescription", response_model=AppointmentSchema)
async def upload_prescription(
    appointment_id: UUID, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: Upload a PDF/Image prescription after the clinic visit.
    Saves locally and updates the database URL.
    """
    db_appointment = crud_appointment.get_appointment(db, appointment_id=appointment_id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Validate file type (optional but recommended)
    if not file.filename.endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Invalid file format. Use PDF or Images.")

    # Create the upload directory if it doesn't exist
    upload_dir = "./uploads/prescriptions"
    os.makedirs(upload_dir, exist_ok=True)

    # Securely save the file asynchronously
    file_extension = file.filename.split(".")[-1]
    file_path = f"{upload_dir}/app_{appointment_id}.{file_extension}"
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # Update database record: Set URL and mark as completed
    public_url = f"/uploads/prescriptions/app_{appointment_id}.{file_extension}"
    
    appointment_update = AppointmentUpdate(
        prescription_url=public_url,
        status="COMPLETED"
    )
    
    return crud_appointment.update_appointment(db=db, db_appointment=db_appointment, appointment_update=appointment_update)

@router.delete("/admin/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(
    appointment_id: UUID, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: Remove a canceled or invalid appointment inquiry.
    """
    db_appointment = crud_appointment.get_appointment(db, appointment_id=appointment_id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    crud_appointment.delete_appointment(db=db, db_appointment=db_appointment)
    return None

@router.get("/appointments/{appointment_id}/download-prescription")
def download_custom_prescription(appointment_id: UUID, db: Session = Depends(get_db)):
    """
    Patient/Admin Action: Downloads a custom PDF stamped with Patient & Doctor details
    using 'F Dr Pad.pdf' as the base template.
    """
    # 1. Fetch Appointment and Doctor details from DB
    db_appointment = crud_appointment.get_appointment(db, appointment_id=appointment_id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    form_details = db_appointment.form_details or {}
    patient_name = form_details.get("patient_name", "Unknown Patient")
    age = form_details.get("age", "--")
    gender = form_details.get("gender", "--")
    
    # Get Doctor Name via the relationship (assuming db_appointment.doctor is loaded)
    doctor_name = db_appointment.doctor.name if db_appointment.doctor else "Assigned Doctor"
    
    # Format the date (Use preferred_date or created_at)
    date_str = db_appointment.preferred_date.strftime("%d/%m/%Y") if db_appointment.preferred_date else datetime.now().strftime("%d/%m/%Y")

    # 2. Create a virtual transparent PDF layer using ReportLab
    packet = io.BytesIO()
    
    # A4 size is roughly 595 x 842 points. Origin (0,0) is bottom-left.
    # Note: You may need to tweak these X, Y coordinates to perfectly align with your F Dr Pad.pdf
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFont("Helvetica-Bold", 11)
    
    # Injecting the dynamic values onto the PDF
    # Format: can.drawString(X_Coordinate, Y_Coordinate, "Text")
    
    # Date at the top middle as requested
    can.drawString(260, 800, f"Date: {date_str}")
    
    # Line 1: Patient's Name, Age, Sex (Aligned to Y=708)
    can.drawString(150, 716, patient_name) # Next to "Patient's Name:"
    can.drawString(437, 716, str(age))     # Next to "Age:"
    can.drawString(529, 716, gender)       # Next to "Sex:"
    
    # Add the Doctor's name prominently at the top or in the designated area
    can.setFont("Helvetica-Bold", 14)
    can.drawString(50, 750, f"Consulting Doctor: {doctor_name}")
    
    can.save()
    packet.seek(0)
    
    # 3. Merge the transparent layer over your existing template
    try:
        # Load your specific blank template (Make sure this file is in your server's root folder)
        existing_pdf = PdfReader(open("assets/F Dr Pad.pdf", "rb"))
        new_pdf = PdfReader(packet)
        output = PdfWriter()
        
        # Merge the first page
        page = existing_pdf.pages[0]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)
        
        # If the template has more than 1 page, append them as well
        for i in range(1, len(existing_pdf.pages)):
            output.add_page(existing_pdf.pages[i])
            
        # 4. Save to a stream and return to the user
        output_stream = io.BytesIO()
        output.write(output_stream)
        output_stream.seek(0)
        
        file_name = f"Prescription_{patient_name.replace(' ', '_')}.pdf"
        
        return StreamingResponse(
            output_stream, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'}
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Template F Dr Pad.pdf not found on server")
