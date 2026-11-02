import strawberry
from typing import Optional, List
from uuid import UUID
from sqlalchemy import or_

from graphql_api.types.shop import ShopType, InventoryItemType, ShopBillType
from models.shop import Shop as ShopModel
from models.inventory import InventoryItem as InventoryItemModel
from models.shop_bill import ShopBill as ShopBillModel
from models.database import get_db

@strawberry.type
class ShopQuery:
    
    @strawberry.field
    def get_shops(self) -> List[ShopType]:
        """
        Admin View: Fetches all physical pharmacy branches/locations.
        """
        db = next(get_db())
        return db.query(ShopModel).order_by(ShopModel.created_at.desc()).all()

    @strawberry.field
    def get_inventory(
        self, 
        shop_id: UUID, 
        search_term: Optional[str] = None,
        low_stock_only: bool = False,
        limit: int = 50, 
        skip: int = 0
    ) -> List[InventoryItemType]:
        """
        Admin View: Powers the inventory data tables. Includes search functionality
        and a toggle to quickly find medications that need to be reordered.
        """
        db = next(get_db())
        query = db.query(InventoryItemModel).filter(InventoryItemModel.shop_id == shop_id)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    InventoryItemModel.name.ilike(search_pattern),
                    InventoryItemModel.sku.ilike(search_pattern)
                )
            )
            
        if low_stock_only:
            # Assuming stock under 10 is considered low
            query = query.filter(InventoryItemModel.stock_quantity <= 10)
            
        return query.order_by(InventoryItemModel.name.asc()).offset(skip).limit(limit).all()

    @strawberry.field
    def get_shop_bills(
        self, 
        shop_id: UUID, 
        limit: int = 50, 
        skip: int = 0
    ) -> List[ShopBillType]:
        """
        Admin View: Fetches the point-of-sale transaction history for a specific branch.
        """
        db = next(get_db())
        
        return (
            db.query(ShopBillModel)
            .filter(ShopBillModel.shop_id == shop_id)
            .order_by(ShopBillModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
