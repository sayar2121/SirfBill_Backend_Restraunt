import strawberry
from typing import Optional
from uuid import UUID

from graphql_api.types.user import UserType 
from crud import user as crud_user
from models.database import get_db

@strawberry.type
class UserQuery:
    @strawberry.field
    def get_user_profile(self, user_id: UUID) -> Optional[UserType]:
        """
        The Master Query: Fetches the user and all their nested relationships 
        (appointments, lab_bookings) in one go.
        """
        # Get the database session (using next() since get_db is usually a generator)
        db = next(get_db())
        
        db_user = crud_user.get_user(db, user_id=user_id)
        
        if not db_user:
            return None
            
        # Strawberry automatically resolves the SQLAlchemy model into the UserType
        # Thanks to your ConfigDict and attribute mapping!
        return db_user
