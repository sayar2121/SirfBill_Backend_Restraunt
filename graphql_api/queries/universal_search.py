import strawberry
from typing import List, Optional
from sqlalchemy import or_

from graphql_api.types.doctor import DoctorType
from graphql_api.types.lab_catalog import LabCatalogType
from models.doctor import Doctor as DoctorModel
from models.lab_catalog import LabCatalog as LabCatalogModel
from models.database import get_db

@strawberry.type
class GlobalSearchResult:
    """
    A unified response type that returns both doctors and lab tests 
    matching the user's search query in one go.
    """
    doctors: List[DoctorType]
    lab_tests: List[LabCatalogType]

@strawberry.type
class UniversalSearchQuery:
    
    @strawberry.field
    def global_search(self, search_term: str, limit: int = 5) -> GlobalSearchResult:
        """
        Type 2 Search: Searches everything at once. Perfect for the Home Screen search bar!
        Returns a maximum of 5 doctors and 5 lab tests to keep the UI fast.
        """
        db = next(get_db())
        search_pattern = f"%{search_term}%"
        
        # 1. Search Doctors
        doctors = (
            db.query(DoctorModel)
            .filter(
                or_(
                    DoctorModel.name.ilike(search_pattern),
                    DoctorModel.specialty_key.ilike(search_pattern)
                )
            )
            .limit(limit)
            .all()
        )
        
        # 2. Search Lab Tests
        lab_tests = (
            db.query(LabCatalogModel)
            .filter(LabCatalogModel.title.ilike(search_pattern))
            .limit(limit)
            .all()
        )
        
        return GlobalSearchResult(doctors=doctors, lab_tests=lab_tests)
