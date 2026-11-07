from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID

from models.database import get_db 
from models.inventory import InventoryItem
from models.category import Category
from models.rack import Rack
from models.distributor import Distributor
from models.user import User
from models.shop_bill import ShopBill
from models.restaurant_menu import RestaurantMenuItem
from models.restaurant_order import RestaurantOrder
from models.restaurant_customer import RestaurantCustomer
from dependencies import get_optional_restaurant_staff

router = APIRouter(
    prefix="/api",
    tags=["Search"]
)

@router.get("/search")
def search_inventory(
    q: str = Query(..., min_length=2, description="Search by name, sku, or manufacturer"),
    shop_id: Optional[UUID] = None,
    limit: int = Query(20, description="Max results to return"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    """
    Optimized inventory search using GIN/Trigram index lookup.
    Scopes by tenant/shop first to avoid full table scans.
    """
    target_shop = shop_id
    if not target_shop and current_user and current_user.shop_id:
        target_shop = current_user.shop_id

    # 1. Scope query by shop / tenant first
    query = db.query(InventoryItem).filter(
        InventoryItem.is_deleted == 0,
        InventoryItem.stock_quantity > 0
    )
    if target_shop:
        query = query.filter(InventoryItem.shop_id == target_shop)
    elif current_user and current_user.tenant_id:
        query = query.filter(InventoryItem.tenant_id == current_user.tenant_id)

    tokens = [t.strip() for t in q.strip().split() if t.strip()]
    for token in tokens:
        search_term = f"%{token}%"
        # Pure indexed text columns - NO runtime cast(column, String)
        query = query.filter(
            or_(
                InventoryItem.name.ilike(search_term),
                InventoryItem.sku.ilike(search_term),
                InventoryItem.manufacturer.ilike(search_term),
                InventoryItem.batch_number.ilike(search_term),
                InventoryItem.hsn_code.ilike(search_term)
            )
        )

    results = query.limit(limit).all()

    if not results:
        return {
            "status": "success", 
            "data": [], 
            "message": "No items found matching your query."
        }

    return {
        "status": "success",
        "count": len(results),
        "data": results
    }

@router.get("/admin/search/global")
def global_search(
    q: str = Query(..., min_length=2, description="Search across restaurant dishes, guests, and orders"),
    outlet_id: Optional[UUID] = None,
    limit: int = Query(8, description="Max results per category"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    """
    High-speed Global Search scoped by tenant/outlet first.
    Uses GIN Trigram indexes on millions of rows.
    """
    target_outlet = outlet_id
    if not target_outlet and current_user and current_user.outlet_id:
        target_outlet = current_user.outlet_id

    search_term = f"%{q.strip()}%"

    # 1. Search Restaurant Menu Items (Scoped by outlet_id)
    menu_query = db.query(RestaurantMenuItem).filter(RestaurantMenuItem.is_active == True)
    if target_outlet:
        menu_query = menu_query.filter(RestaurantMenuItem.outlet_id == target_outlet)
    elif current_user and current_user.tenant_id:
        menu_query = menu_query.filter(RestaurantMenuItem.tenant_id == current_user.tenant_id)

    dishes = menu_query.filter(
        or_(
            RestaurantMenuItem.name.ilike(search_term),
            RestaurantMenuItem.short_code.ilike(search_term)
        )
    ).limit(limit).all()

    # 2. Search Restaurant Guests / Customers (Scoped by outlet/tenant)
    cust_query = db.query(RestaurantCustomer).filter(RestaurantCustomer.is_active == True)
    if target_outlet:
        cust_query = cust_query.filter(RestaurantCustomer.outlet_id == target_outlet)
    elif current_user and current_user.tenant_id:
        cust_query = cust_query.filter(RestaurantCustomer.tenant_id == current_user.tenant_id)

    customers = cust_query.filter(
        or_(
            RestaurantCustomer.name.ilike(search_term),
            RestaurantCustomer.phone.ilike(search_term)
        )
    ).limit(limit).all()

    # 3. Search Orders (Scoped by outlet/tenant, indexed on order_number & phone)
    order_query = db.query(RestaurantOrder)
    if target_outlet:
        order_query = order_query.filter(RestaurantOrder.outlet_id == target_outlet)
    elif current_user and current_user.tenant_id:
        order_query = order_query.filter(RestaurantOrder.tenant_id == current_user.tenant_id)

    orders = order_query.filter(
        or_(
            RestaurantOrder.order_number.ilike(search_term),
            RestaurantOrder.customer_phone.ilike(search_term),
            RestaurantOrder.customer_name.ilike(search_term)
        )
    ).order_by(RestaurantOrder.created_at.desc()).limit(limit).all()

    return {
        "status": "success",
        "data": {
            "dishes": [
                {
                    "id": str(d.id),
                    "name": d.name,
                    "short_code": d.short_code,
                    "category_id": str(d.category_id) if d.category_id else None,
                    "is_available": d.is_available
                }
                for d in dishes
            ],
            "customers": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "phone": c.phone
                }
                for c in customers
            ],
            "orders": [
                {
                    "id": str(o.id),
                    "order_number": o.order_number,
                    "status": o.status,
                    "grand_total": float(o.grand_total or 0.0),
                    "created_at": o.created_at.isoformat() if o.created_at else None
                }
                for o in orders
            ]
        }
    }
