import strawberry
from typing import Optional, List
from uuid import UUID

from graphql_api.types.appointment import AppointmentType 
from models.appointment import Appointment as AppointmentModel
from models.database import get_db
from models.enums import BookingStatus

@strawberry.type
class AppointmentQuery:
    
    @strawberry.field
    def get_appointment(self, appointment_id: UUID) -> Optional[AppointmentType]:
        """
        Fetches the specific details of a single appointment.
        Note: The user's entire appointment history is already fetched 
        in the UserQuery via the `appointments` relationship.
        """
        db = next(get_db())
        
        db_appointment = db.query(AppointmentModel).filter(AppointmentModel.id == appointment_id).first()
        
        if not db_appointment:
            return None
            
        return db_appointment

    @strawberry.field
    def get_admin_pending_appointments(self, info: strawberry.Info, limit: int = 50) -> List[AppointmentType]:
        """
        Admin View: Fetches a list of pending appointments that need to be confirmed.
        (Can also be used with the Delta Polling strategy in REST, but provided here for flexibility)
        """
        # 🛡️ SECURE: Check the context injected by FastAPI
        if info.context.get("role") != "ADMIN":
            raise Exception("Unauthorized access. Admin privileges required.")
            
        db = next(get_db())
        
        db_appointments = (
            db.query(AppointmentModel)
            .filter(AppointmentModel.status == BookingStatus.PENDING_CONFIRMATION)
            .order_by(AppointmentModel.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return db_appointments

    @strawberry.field
    def get_admin_appointments(self, info: strawberry.Info, status: Optional[str] = None, limit: int = 100) -> List[AppointmentType]:
        """
        Admin View: Fetches a list of all appointments, optionally filtered by status.
        Status should match the exact uppercase values (e.g. "CONFIRMED", "COMPLETED").
        """
        # 🛡️ SECURE: Check the context injected by FastAPI
        if info.context.get("role") != "ADMIN":
            raise Exception("Unauthorized access. Admin privileges required.")
            
        db = next(get_db())
        
        query = db.query(AppointmentModel)
        
        if status:
            query = query.filter(AppointmentModel.status == status)
            
        db_appointments = (
            query.order_by(AppointmentModel.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return db_appointments
