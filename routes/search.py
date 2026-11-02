from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.database import get_db 
from models.inventory import InventoryItem
from models.category import Category
from models.rack import Rack
from models.distributor import Distributor
from models.user import User
from models.shop_bill import ShopBill
from sqlalchemy import cast, String

router = APIRouter(
    prefix="/api",
    tags=["Search"]
)

@router.get("/search")
def search_medicine_inventory(
    q: str = Query(..., min_length=2, description="Search by medicine name, sku, or manufacturer"),
    limit: int = Query(20, description="Max results to return"),
    db: Session = Depends(get_db)
):
    # 1. THE QUERY: Case-insensitive search using 'ilike'
    # The f"%{q}%" adds wildcards so it matches partial words
    query = (
        db.query(InventoryItem)
        .outerjoin(Category, InventoryItem.category_id == Category.id)
        .outerjoin(Rack, InventoryItem.rack_id == Rack.id)
        .outerjoin(Distributor, InventoryItem.distributor_id == Distributor.id)
        .filter(InventoryItem.is_deleted == 0)
        .filter(InventoryItem.stock_quantity > 0)
    )
    tokens = [t.strip() for t in q.strip().split() if t.strip()]
    for token in tokens:
        search_term = f"%{token}%"
        query = query.filter(
            or_(
                InventoryItem.name.ilike(search_term),
                InventoryItem.sku.ilike(search_term),
                InventoryItem.manufacturer.ilike(search_term),
                InventoryItem.batch_number.ilike(search_term),
                InventoryItem.hsn_code.ilike(search_term),
                InventoryItem.distributor.ilike(search_term),
                Distributor.name.ilike(search_term),
                Category.name.ilike(search_term),
                Category.description.ilike(search_term),
                Rack.rack_number.ilike(search_term),
                Rack.details.ilike(search_term),
                cast(InventoryItem.expiry_date, String).ilike(search_term),
                cast(InventoryItem.unit_price, String).ilike(search_term),
                cast(InventoryItem.buying_price, String).ilike(search_term),
            )
        )
    results = query.limit(limit).all()

    # 2. THE RESPONSE
    if not results:
        return {
            "status": "success", 
            "data": [], 
            "message": "No medicines found matching your query."
        }

    return {
        "status": "success",
        "count": len(results),
        "data": results
    }

@router.get("/admin/search/global")
def global_search(
    q: str = Query(..., min_length=2, description="Search everything"),
    limit: int = Query(5, description="Max results per category"),
    db: Session = Depends(get_db)
):
    search_term = f"%{q}%"
    
    # 1. Search Medicines
    med_query = (
        db.query(InventoryItem)
        .outerjoin(Category, InventoryItem.category_id == Category.id)
        .outerjoin(Rack, InventoryItem.rack_id == Rack.id)
        .outerjoin(Distributor, InventoryItem.distributor_id == Distributor.id)
        .filter(InventoryItem.is_deleted == 0)
    )
    for token in [t.strip() for t in q.strip().split() if t.strip()]:
        term = f"%{token}%"
        med_query = med_query.filter(
            or_(
                InventoryItem.name.ilike(term),
                InventoryItem.sku.ilike(term),
                InventoryItem.manufacturer.ilike(term),
                InventoryItem.batch_number.ilike(term),
                InventoryItem.hsn_code.ilike(term),
                InventoryItem.distributor.ilike(term),
                Distributor.name.ilike(term),
                Category.name.ilike(term),
                Category.description.ilike(term),
                Rack.rack_number.ilike(term),
                Rack.details.ilike(term),
                cast(InventoryItem.expiry_date, String).ilike(term),
                cast(InventoryItem.unit_price, String).ilike(term),
                cast(InventoryItem.buying_price, String).ilike(term),
            )
        )
    medicines = med_query.limit(limit).all()
    
    # 2. Search Customers
    customers = (
        db.query(User)
        .filter(
            or_(
                User.name.ilike(search_term),
                User.phone.ilike(search_term)
            )
        )
        .limit(limit)
        .all()
    )
    
    # 3. Search Invoices
    # Only matching exact UUID or casting UUID to string to search via ilike (which is tricky).
    # Since invoice numbers are typically UUIDs in this system, let's search via string cast.
    from sqlalchemy import cast, String
    invoices = (
        db.query(ShopBill)
        .filter(cast(ShopBill.id, String).ilike(search_term))
        .limit(limit)
        .all()
    )
    
    return {
        "status": "success",
        "data": {
            "medicines": [
                {"id": str(m.id), "name": m.name, "sku": m.sku, "stock": m.stock_quantity, "price": m.unit_price}
                for m in medicines
            ],
            "customers": [
                {"id": str(c.id), "name": c.name, "phone": c.phone}
                for c in customers
            ],
            "invoices": [
                {"id": str(i.id), "date": i.created_at.isoformat(), "amount": i.total_amount}
                for i in invoices
            ]
        }
    }
