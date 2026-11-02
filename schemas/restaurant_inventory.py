from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

# Ingredients
class RestaurantIngredientBase(BaseModel):
    name: str = Field(..., max_length=150)
    sku: Optional[str] = None
    unit: str = "KG" # KG, G, L, ML, PCS
    current_stock: Decimal = Decimal("0.000")
    reorder_level: Decimal = Decimal("5.000")
    cost_per_unit: Decimal = Decimal("0.00")
    is_active: bool = True

class RestaurantIngredientCreate(RestaurantIngredientBase):
    outlet_id: UUID

class RestaurantIngredientResponse(RestaurantIngredientBase):
    id: UUID
    outlet_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Stock Ledger
class StockAdjustmentCreate(BaseModel):
    ingredient_id: UUID
    signed_quantity: Decimal # Positive for addition, Negative for wastage
    reason: str # PURCHASE_RECEIVED, WASTAGE, PHYSICAL_COUNT_ADJUSTMENT
    notes: Optional[str] = None

class StockLedgerResponse(BaseModel):
    id: UUID
    ingredient_id: UUID
    outlet_id: UUID
    tenant_id: UUID
    signed_quantity: Decimal
    reason: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    actor_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Recipe
class RecipeLineInput(BaseModel):
    ingredient_id: UUID
    quantity_required: Decimal
    unit: str

class RecipeCreate(BaseModel):
    item_id: UUID
    variant_name: str = "Standard"
    yield_servings: Decimal = Decimal("1.00")
    instructions: Optional[str] = None
    lines: List[RecipeLineInput] = []

class RecipeLineResponse(BaseModel):
    id: UUID
    ingredient_id: UUID
    quantity_required: Decimal
    unit: str

    model_config = ConfigDict(from_attributes=True)

class RecipeResponse(BaseModel):
    id: UUID
    item_id: UUID
    variant_name: str
    yield_servings: Decimal
    instructions: Optional[str] = None
    lines: List[RecipeLineResponse] = []

    model_config = ConfigDict(from_attributes=True)
