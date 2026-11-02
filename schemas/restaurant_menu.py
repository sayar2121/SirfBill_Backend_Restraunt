from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, computed_field

# Menu Categories
class RestaurantMenuCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    icon_emoji: Optional[str] = "🍽️"
    sort_order: int = 0
    is_active: bool = True

    model_config = ConfigDict(extra="allow", from_attributes=True)

class RestaurantMenuCategoryCreate(RestaurantMenuCategoryBase):
    outlet_id: Optional[UUID] = None

class RestaurantMenuCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon_emoji: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="allow")

class RestaurantMenuCategoryResponse(RestaurantMenuCategoryBase):
    id: UUID
    outlet_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Item Prices
class RestaurantItemPriceBase(BaseModel):
    variant_name: str = "Standard"
    channel: str = "DEFAULT"
    price: Decimal = Field(..., ge=0)

class RestaurantItemPriceCreate(RestaurantItemPriceBase):
    pass

class RestaurantItemPriceResponse(RestaurantItemPriceBase):
    id: UUID
    item_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Menu Items
class RestaurantMenuItemBase(BaseModel):
    name: str = Field(..., max_length=150)
    short_code: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    item_type: str = "NON_VEG" # VEG, NON_VEG, EGG, VEGAN
    prep_station: str = "KITCHEN" # KITCHEN, BAR, DESSERT, PIZZA
    tax_rate: Decimal = Decimal("5.00")
    price: Optional[Decimal] = Decimal("0.00")
    badge: Optional[str] = None
    is_available: bool = True
    is_active: bool = True

    model_config = ConfigDict(extra="allow", from_attributes=True)

class RestaurantMenuItemCreate(RestaurantMenuItemBase):
    outlet_id: Optional[UUID] = None
    category_id: Optional[Any] = None
    price: Optional[Decimal] = None
    is_veg: Optional[bool] = None
    badge: Optional[str] = None
    prices: List[RestaurantItemPriceCreate] = []
    modifier_group_ids: List[UUID] = []

    model_config = ConfigDict(extra="allow")

class RestaurantMenuItemUpdate(BaseModel):
    category_id: Optional[Any] = None
    name: Optional[str] = None
    short_code: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    item_type: Optional[str] = None
    is_veg: Optional[bool] = None
    price: Optional[Decimal] = None
    badge: Optional[str] = None
    prep_station: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="allow")

class RestaurantMenuItemResponse(RestaurantMenuItemBase):
    id: UUID
    outlet_id: UUID
    tenant_id: UUID
    category_id: Optional[UUID] = None
    prices: List[RestaurantItemPriceResponse] = []
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_veg(self) -> bool:
        return self.item_type == "VEG"

    model_config = ConfigDict(from_attributes=True)
