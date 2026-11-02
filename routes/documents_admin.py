from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import io
from jinja2 import Environment, FileSystemLoader # For HTML templating[cite: 1]
# WeasyPrint requires system GTK libs (libgobject). Import lazily to avoid crash on startup if missing.
try:
    from weasyprint import HTML
except Exception:
    HTML = None

from models.database import get_db
from dependencies import get_admin_user
from models.user import User

router = APIRouter(
    prefix="/api/admin/documents",
    tags=["Admin - Document Generation"]
)

# Setup Jinja2 template environment[cite: 1]
template_env = Environment(loader=FileSystemLoader(searchpath="./templates"))

@router.get("/prescription/{appointment_id}/pdf")
def generate_prescription_pdf(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin/Doctor Action: Dynamically generates a PDF prescription and streams it to the client[cite: 1].
    """
    # 1. Fetch data from DB
    from crud import appointment as crud_appointment
    db_appt = crud_appointment.get_appointment(db, appointment_id)
    if not db_appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # 2. Prepare dynamic data for the template[cite: 1]
    template_data = {
        "patient_name": db_appt.user.name,
        "doctor_name": db_appt.doctor.name if db_appt.doctor else "Doctor",
        "date": db_appt.preferred_date.strftime("%B %d, %Y"),
        "medications": db_appt.form_details.get("medications", []) if db_appt.form_details else [],
        "notes": db_appt.form_details.get("clinical_notes", "No additional notes.") if db_appt.form_details else ""
    }

    # 3. Render HTML using Jinja2[cite: 1]
    template = template_env.get_template("prescription_template.html")
    html_out = template.render(template_data)

    # 4. Convert HTML to PDF using WeasyPrint[cite: 1]
    if HTML is None:
        raise HTTPException(status_code=503, detail="PDF generation not available: WeasyPrint system libraries missing.")
    pdf_bytes = HTML(string=html_out).write_pdf()

    # 5. Return as a StreamingResponse directly to bypass disk writes[cite: 1]
    return StreamingResponse(
        io.BytesIO(pdf_bytes), 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"inline; filename=prescription_{appointment_id}.pdf"}
    )
