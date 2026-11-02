from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from dependencies import get_admin_user
from models.user import User
from models.payment import Payment
from models.lab_booking import LabBooking
from models.appointment import Appointment
from models.enums import BookingStatus

router = APIRouter(
    prefix="/api/admin/dashboard",
    tags=["Admin - Dashboard Stats"]
)

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin Action: Fetches the high-level numbers for the Admin Home Screen.
    """
    # 1. Total Revenue (Sum of all SUCCESSFUL payments)
    total_revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == "SUCCESS").scalar() or 0.0

    # 2. Total Registered Patients (Users who are not admins)
    total_patients = db.query(User).filter(User.role == "USER").count()

    # 3. Action Items (Things the admin needs to do TODAY)
    pending_lab_bookings = db.query(LabBooking).filter(LabBooking.status == BookingStatus.PENDING_CONFIRMATION).count()
    pending_appointments = db.query(Appointment).filter(Appointment.status == BookingStatus.PENDING_CONFIRMATION).count()

    return {
        "total_revenue": total_revenue,
        "total_patients": total_patients,
        "actionable_items": {
            "pending_lab_bookings": pending_lab_bookings,
            "pending_appointments": pending_appointments
        }
    }
