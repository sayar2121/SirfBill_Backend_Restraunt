from sqlalchemy.orm import Session
from models.banner import Banner
from schemas.banner import BannerCreate, BannerUpdate
from uuid import UUID

def get_banners(db: Session, include_inactive: bool = False):
    query = db.query(Banner)
    if not include_inactive:
        query = query.filter(Banner.is_active == True)
    return query.order_by(Banner.created_at.desc()).all()

def create_banner(db: Session, banner: BannerCreate) -> Banner:
    db_banner = Banner(**banner.model_dump())
    db.add(db_banner)
    db.commit()
    db.refresh(db_banner)
    return db_banner

def update_banner(db: Session, banner_id: UUID, banner_update: BannerUpdate) -> Banner:
    db_banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not db_banner:
        return None
    
    update_data = banner_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_banner, key, value)
    
    db.commit()
    db.refresh(db_banner)
    return db_banner

def delete_banner(db: Session, banner_id: UUID) -> bool:
    db_banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if db_banner:
        db.delete(db_banner)
        db.commit()
        return True
    return False
