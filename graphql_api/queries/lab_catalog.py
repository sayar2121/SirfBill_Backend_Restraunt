import strawberry
from typing import Optional, List
from uuid import UUID
from sqlalchemy import or_

from graphql_api.types.lab_catalog import LabCatalogType 
from models.lab_catalog import LabCatalog as LabCatalogModel
from models.database import get_db

@strawberry.type
class LabCatalogQuery:
    
    @strawberry.field
    def get_lab_catalog(
        self, 
        type_filter: Optional[str] = None, 
        search_term: Optional[str] = None,
        limit: int = 20, 
        skip: int = 0
    ) -> List[LabCatalogType]:
        """
        Discovery Query: Fetches the catalog with optional type filtering and search.
        """
        db = next(get_db())
        query = db.query(LabCatalogModel)
        
        if type_filter:
            query = query.filter(LabCatalogModel.type == type_filter)
            
        if search_term:
            # ILIKE makes it case-insensitive. Search by title.
            search_pattern = f"%{search_term}%"
            query = query.filter(LabCatalogModel.title.ilike(search_pattern))
            
        db_items = query.offset(skip).limit(limit).all()
        return db_items

    @strawberry.field
    def get_lab_item_by_id(self, item_id: UUID) -> Optional[LabCatalogType]:
        db = next(get_db())
        db_item = db.query(LabCatalogModel).filter(LabCatalogModel.id == item_id).first()
        if not db_item:
            return None
        return db_item
