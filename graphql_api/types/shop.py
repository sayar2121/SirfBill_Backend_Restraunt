import strawberry
from typing import Optional, List, Annotated
from uuid import UUID
from datetime import datetime, date

@strawberry.type
class ShopType:
    id: UUID
    tenant_id: Optional[UUID]
    name: str
    address: str
    contact_number: Optional[str]
    created_at: datetime

@strawberry.type
class InventoryItemType:
    id: UUID
    tenant_id: Optional[UUID]
    shop_id: UUID
    name: str
    sku: str
    manufacturer: Optional[str]
    batch_number: Optional[str]
    stock_quantity: int
    unit_price: float
    expiry_date: Optional[date] = None
    created_at: datetime
    
    # Resolves the branch this item belongs to
    shop: Annotated["ShopType", strawberry.lazy("graphql_api.types.shop")]

@strawberry.type
class ShopBillItemType:
    id: UUID
    inventory_item_id: UUID
    quantity: int
    unit_price_at_sale: float
    
    item: Annotated["InventoryItemType", strawberry.lazy("graphql_api.types.shop")]

@strawberry.type
class ShopBillType:
    id: UUID
    tenant_id: Optional[UUID]
    shop_id: UUID
    user_id: Optional[UUID]
    prescription_id: Optional[UUID]
    total_amount: float
    payment_method: str
    status: str
    created_at: datetime
    
    # Resolves the line items for the receipt
    items: List[ShopBillItemType]
