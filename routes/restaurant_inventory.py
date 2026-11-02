from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from models.database import get_db
from models.user import User
from models.restaurant_outlet import RestaurantOutlet
from models.restaurant_ingredient import RestaurantIngredient
from models.restaurant_recipe import RestaurantRecipe, RestaurantRecipeLine
from models.restaurant_stock_ledger import RestaurantStockLedger
from schemas.restaurant_inventory import (
    RestaurantIngredientCreate, RestaurantIngredientResponse,
    StockAdjustmentCreate, StockLedgerResponse,
    RecipeCreate, RecipeResponse
)
from dependencies import get_restaurant_staff, get_restaurant_manager

router = APIRouter(
    prefix="/api/restaurant/inventory",
    tags=["Restaurant - Ingredients & Recipes"]
)

# ----------------- INGREDIENTS -----------------

@router.get("/ingredients", response_model=List[RestaurantIngredientResponse])
def get_ingredients(
    outlet_id: UUID,
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_staff)
):
    query = (
        db.query(RestaurantIngredient)
        .filter(RestaurantIngredient.outlet_id == outlet_id)
        .filter(RestaurantIngredient.is_active == True)
    )
    if low_stock_only:
        query = query.filter(RestaurantIngredient.current_stock <= RestaurantIngredient.reorder_level)

    return query.order_by(RestaurantIngredient.name.asc()).all()


@router.post("/ingredients", response_model=RestaurantIngredientResponse, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    payload: RestaurantIngredientCreate,
    db: Session = Depends(get_db),
    manager_user: User = Depends(get_restaurant_manager)
):
    outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == payload.outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Restaurant outlet not found")

    ingredient = RestaurantIngredient(
        outlet_id=payload.outlet_id,
        tenant_id=outlet.tenant_id,
        name=payload.name,
        sku=payload.sku,
        unit=payload.unit.upper(),
        current_stock=payload.current_stock,
        reorder_level=payload.reorder_level,
        cost_per_unit=payload.cost_per_unit,
        is_active=payload.is_active
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


@router.post("/adjustments", response_model=StockLedgerResponse, status_code=status.HTTP_201_CREATED)
def record_stock_adjustment(
    payload: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    manager_user: User = Depends(get_restaurant_manager)
):
    """
    Append-only stock ledger adjustment. Modifies current stock balance atomically.
    """
    ingredient = db.query(RestaurantIngredient).filter(RestaurantIngredient.id == payload.ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    signed_qty = Decimal(str(payload.signed_quantity))

    ledger_entry = RestaurantStockLedger(
        ingredient_id=ingredient.id,
        outlet_id=ingredient.outlet_id,
        tenant_id=ingredient.tenant_id,
        signed_quantity=signed_qty,
        reason=payload.reason,
        source_type="manual",
        actor_id=manager_user.id,
        notes=payload.notes
    )
    db.add(ledger_entry)

    # Atomically adjust current cached balance
    ingredient.current_stock += signed_qty

    db.commit()
    db.refresh(ledger_entry)
    return ledger_entry


# ----------------- RECIPES / BOM -----------------

@router.post("/recipes", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    payload: RecipeCreate,
    db: Session = Depends(get_db),
    manager_user: User = Depends(get_restaurant_manager)
):
    """
    Define Bill of Materials (BOM) linking menu dish/variant to required ingredients.
    """
    recipe = RestaurantRecipe(
        item_id=payload.item_id,
        variant_name=payload.variant_name,
        yield_servings=payload.yield_servings,
        instructions=payload.instructions
    )
    db.add(recipe)
    db.flush()

    for line in payload.lines:
        r_line = RestaurantRecipeLine(
            recipe_id=recipe.id,
            ingredient_id=line.ingredient_id,
            quantity_required=line.quantity_required,
            unit=line.unit.upper()
        )
        db.add(r_line)

    db.commit()
    db.refresh(recipe)
    return recipe


@router.get("/recipes/{item_id}", response_model=List[RecipeResponse])
def get_item_recipes(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_staff)
):
    return (
        db.query(RestaurantRecipe)
        .options(joinedload(RestaurantRecipe.lines))
        .filter(RestaurantRecipe.item_id == item_id)
        .all()
    )
