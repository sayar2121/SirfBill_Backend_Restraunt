import strawberry
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from models.banner import Banner as BannerModel
from models.database import get_db

@strawberry.type
class BannerType:
    id: UUID
    image_url: str
    action_url: Optional[str]
    is_active: bool
    created_at: datetime

@strawberry.type
class BannerQuery:
    
    @strawberry.field
    def get_active_banners(self) -> List[BannerType]:
        """
        Fetches all active advertisement banners for the Flutter Home Screen Carousel.
        """
        db = next(get_db())
        
        # Only fetch banners where is_active is True
        banners = db.query(BannerModel).filter(BannerModel.is_active == True).all()
        
        return banners
