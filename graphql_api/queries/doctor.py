import strawberry
from typing import Optional, List
from uuid import UUID
from sqlalchemy import or_

from graphql_api.types.doctor import DoctorType 
from models.doctor import Doctor as DoctorModel
from models.database import get_db

@strawberry.type
class DoctorQuery:
    
    @strawberry.field
    def get_doctors(
        self, 
        specialty_key: Optional[str] = None, 
        search_term: Optional[str] = None,
        limit: int = 10, 
        skip: int = 0
    ) -> List[DoctorType]:
        """
        Discovery Query: Fetches a list of doctors with optional filtering and search.
        """
        db = next(get_db())
        query = db.query(DoctorModel)
        
        if specialty_key:
            query = query.filter(DoctorModel.specialty_key == specialty_key)
            
        if search_term:
            # ILIKE makes it case-insensitive. We search by name or specialty.
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    DoctorModel.name.ilike(search_pattern),
                    DoctorModel.specialty_key.ilike(search_pattern)
                )
            )
            
        db_doctors = query.offset(skip).limit(limit).all()
        return db_doctors

    @strawberry.field
    def get_doctor_by_id(self, doctor_id: UUID) -> Optional[DoctorType]:
        db = next(get_db())
        db_doctor = db.query(DoctorModel).filter(DoctorModel.id == doctor_id).first()
        if not db_doctor:
            return None
        return db_doctor
