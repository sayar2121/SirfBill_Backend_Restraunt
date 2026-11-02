from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from models.database import get_db
from dependencies import get_admin_user
from models.user import User
from models.distributor import Distributor
from models.shop_bill import ShopBillItem, ShopBill
from models.inventory import InventoryItem
from schemas.distributor import DistributorCreate, DistributorUpdate, DistributorOut

router = APIRouter(
    prefix="/api/admin/distributors",
    tags=["Admin - Distributors"]
)

@router.post("/", response_model=DistributorOut, status_code=status.HTTP_201_CREATED)
def create_distributor(
    request: DistributorCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    new_distributor = Distributor(
        tenant_id=admin_user.tenant_id,
        **request.model_dump()
    )
    db.add(new_distributor)
    db.commit()
    db.refresh(new_distributor)
    return new_distributor

@router.get("/", response_model=List[DistributorOut])
def get_distributors(
    shop_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    query = db.query(Distributor)
    if shop_id:
        query = query.filter(Distributor.shop_id == shop_id)
    if admin_user.tenant_id:
        query = query.filter(Distributor.tenant_id == admin_user.tenant_id)
        
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(Distributor.name.ilike(search_pattern))
        
    return query.all()

@router.get("/{distributor_id}", response_model=DistributorOut)
def get_distributor(
    distributor_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    distributor = db.query(Distributor).filter(Distributor.id == distributor_id).first()
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    return distributor

@router.patch("/{distributor_id}", response_model=DistributorOut)
def update_distributor(
    distributor_id: UUID,
    request: DistributorUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    distributor = db.query(Distributor).filter(Distributor.id == distributor_id).first()
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
        
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(distributor, key, value)
        
    db.commit()
    db.refresh(distributor)
    return distributor

@router.delete("/{distributor_id}")
def delete_distributor(
    distributor_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    distributor = db.query(Distributor).filter(Distributor.id == distributor_id).first()
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
        
    db.delete(distributor)
    db.commit()
    return {"status": "success", "message": "Distributor deleted successfully"}

@router.get("/{distributor_id}/analytics")
def get_distributor_analytics(
    distributor_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Analytics: See how much of this distributor's medicine has been sold.
    """
    # Find all inventory items supplied by this distributor
    items_supplied = db.query(InventoryItem.id).filter(InventoryItem.distributor_id == distributor_id).subquery()
    
    # Calculate total sales quantity and revenue for these items
    sales_data = db.query(
        func.sum(ShopBillItem.quantity).label("total_quantity_sold"),
        func.sum(ShopBillItem.quantity * ShopBillItem.unit_price_at_sale).label("total_revenue")
    ).filter(ShopBillItem.inventory_item_id.in_(items_supplied)).first()
    
    # Top 5 most sold items from this distributor
    top_items = db.query(
        InventoryItem.name,
        func.sum(ShopBillItem.quantity).label("qty")
    ).join(ShopBillItem, ShopBillItem.inventory_item_id == InventoryItem.id)\
     .filter(InventoryItem.distributor_id == distributor_id)\
     .group_by(InventoryItem.name)\
     .order_by(func.sum(ShopBillItem.quantity).desc())\
     .limit(5).all()
    
    return {
        "distributor_id": distributor_id,
        "total_items_sold": sales_data.total_quantity_sold or 0,
        "total_revenue_generated": sales_data.total_revenue or 0.0,
        "top_selling_medicines": [{"name": i.name, "quantity_sold": i.qty} for i in top_items]
    }
