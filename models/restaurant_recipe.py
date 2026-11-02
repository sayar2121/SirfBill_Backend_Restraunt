import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantRecipe(Base):
    """
    Recipe header for a menu item or variant (Bill of Materials - BOM).
    """
    __tablename__ = "restaurant_recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_menu_items.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_name = Column(String(50), default="Standard", nullable=False)
    yield_servings = Column(Numeric(6, 2), default=1.00, nullable=False)
    instructions = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    item = relationship("RestaurantMenuItem")
    lines = relationship("RestaurantRecipeLine", back_populates="recipe", cascade="all, delete-orphan")


class RestaurantRecipeLine(Base):
    """
    Ingredient quantity needed per serving / batch.
    """
    __tablename__ = "restaurant_recipe_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_recipes.id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_ingredients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    quantity_required = Column(Numeric(12, 3), nullable=False) # e.g. 0.250 KG chicken per biryani
    unit = Column(String(20), nullable=False)

    recipe = relationship("RestaurantRecipe", back_populates="lines")
    ingredient = relationship("RestaurantIngredient", back_populates="recipe_lines")
