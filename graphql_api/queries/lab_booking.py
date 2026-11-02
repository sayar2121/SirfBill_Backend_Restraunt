import strawberry
from typing import Optional, List
from uuid import UUID

from graphql_api.types.lab_booking import LabBookingType 
from models.lab_booking import LabBooking as LabBookingModel
from models.database import get_db
from models.enums import BookingStatus

@strawberry.type
class LabBookingQuery:
    
    @strawberry.field
    def get_lab_booking(self, booking_id: UUID) -> Optional[LabBookingType]:
        """
        Fetches the specific details of a single lab booking.
        Note: The user's entire lab booking history is already fetched 
        in the Master UserQuery via the `lab_bookings` relationship.
        """
        db = next(get_db())
        
        db_booking = db.query(LabBookingModel).filter(LabBookingModel.id == booking_id).first()
        
        if not db_booking:
            return None
            
        return db_booking

    @strawberry.field
    def get_admin_pending_lab_bookings(self, info: strawberry.Info, limit: int = 50) -> List[LabBookingType]:
        """
        Admin View: Fetches a list of pending lab bookings that need to be followed up on.
        """
        # 🛡️ SECURE: Check the context injected by FastAPI
        if info.context.get("role") != "ADMIN":
            raise Exception("Unauthorized access. Admin privileges required.")
            
        db = next(get_db())
        
        db_bookings = (
            db.query(LabBookingModel)
            .filter(LabBookingModel.status == BookingStatus.PENDING_CONFIRMATION)
            .order_by(LabBookingModel.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return db_bookings

    @strawberry.field
    def get_admin_lab_bookings(self, info: strawberry.Info, status: Optional[str] = None, limit: int = 100) -> List[LabBookingType]:
        """
        Admin View: Fetches a list of all lab bookings, optionally filtered by status.
        """
        # 🛡️ SECURE: Check the context injected by FastAPI
        if info.context.get("role") != "ADMIN":
            raise Exception("Unauthorized access. Admin privileges required.")
            
        db = next(get_db())
        
        query = db.query(LabBookingModel)
        
        if status:
            query = query.filter(LabBookingModel.status == status)
            
        db_bookings = (
            query.order_by(LabBookingModel.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return db_bookings
