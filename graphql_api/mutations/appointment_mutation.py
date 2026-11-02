import strawberry
from typing import Optional
from uuid import UUID
from datetime import date
from strawberry.scalars import JSON

from graphql_api.types.appointment import AppointmentType
from schemas.appointment import AppointmentCreate
from crud import appointment as crud_appointment
from models.database import get_db

@strawberry.input
class BookAppointmentInput:
    user_id: UUID
    doctor_id: UUID
    preferred_date: date
    form_details: Optional[JSON] = None

@strawberry.type
class AppointmentMutation:
    
    @strawberry.mutation
    def book_appointment(self, input_data: BookAppointmentInput) -> AppointmentType:
        """
        Patient Action: Books a new appointment with a doctor.
        """
        db = next(get_db())
        
        # 1. Map the GraphQL Input directly into your existing Pydantic schema
        appointment_create = AppointmentCreate(
            user_id=input_data.user_id,
            doctor_id=input_data.doctor_id,
            preferred_date=input_data.preferred_date,
            form_details=input_data.form_details,
            # Status defaults to PENDING_CONFIRMATION per your enum
        )
        
        # 2. Call your untouched, production-safe CRUD function
        db_appointment = crud_appointment.create_appointment(db=db, appointment=appointment_create)
        
        # 3. Return the SQLAlchemy object, which Strawberry resolves into AppointmentType
        return db_appointment
