from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import User
from models.restaurant_outlet import RestaurantOutlet
from models.restaurant_customer import RestaurantCustomer, RestaurantLoyaltyLedger
from schemas.restaurant_crm import (
    RestaurantCustomerCreate, RestaurantCustomerResponse,
    LoyaltyPointsAdjustment, LoyaltyLedgerResponse
)
from dependencies import get_restaurant_staff, get_restaurant_cashier

router = APIRouter(
    prefix="/api/restaurant/crm",
    tags=["Restaurant - Customers & Loyalty"]
)

@router.get("/customers", response_model=List[RestaurantCustomerResponse])
def get_customers(
    outlet_id: Optional[UUID] = None,
    search: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_staff)
):
    """
    Search customers by phone or name for quick bill tagging.
    """
    target_outlet = outlet_id or current_user.outlet_id
    query = (
        db.query(RestaurantCustomer)
        .filter(RestaurantCustomer.is_active == True)
    )
    if target_outlet:
        query = query.filter(RestaurantCustomer.outlet_id == target_outlet)
    elif current_user.tenant_id:
        query = query.filter(RestaurantCustomer.tenant_id == current_user.tenant_id)

    if search:
        query = query.filter(
            (RestaurantCustomer.phone.ilike(f"%{search}%")) |
            (RestaurantCustomer.name.ilike(f"%{search}%"))
        )
    return query.limit(limit).all()


@router.post("/customers", response_model=RestaurantCustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: RestaurantCustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_staff)
):
    """
    Register or update customer profile with preferences.
    """
    existing = (
        db.query(RestaurantCustomer)
        .filter(RestaurantCustomer.outlet_id == payload.outlet_id)
        .filter(RestaurantCustomer.phone == payload.phone)
        .first()
    )
    if existing:
        return existing

    outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == payload.outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Restaurant outlet not found")

    customer = RestaurantCustomer(
        outlet_id=payload.outlet_id,
        tenant_id=outlet.tenant_id,
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        preferences=payload.preferences or {},
        notes=payload.notes,
        loyalty_points=0,
        is_active=payload.is_active
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.post("/customers/{customer_id}/loyalty", response_model=LoyaltyLedgerResponse, status_code=status.HTTP_201_CREATED)
def adjust_loyalty_points(
    customer_id: UUID,
    payload: LoyaltyPointsAdjustment,
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Idempotent loyalty points earning or redemption.
    """
    if payload.idempotency_key:
        existing = (
            db.query(RestaurantLoyaltyLedger)
            .filter(RestaurantLoyaltyLedger.idempotency_key == payload.idempotency_key)
            .first()
        )
        if existing:
            return existing

    customer = db.query(RestaurantCustomer).filter(RestaurantCustomer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if payload.points_delta < 0 and customer.loyalty_points < abs(payload.points_delta):
        raise HTTPException(status_code=400, detail="Insufficient loyalty points balance")

    ledger = RestaurantLoyaltyLedger(
        customer_id=customer.id,
        points_delta=payload.points_delta,
        reason=payload.reason,
        idempotency_key=payload.idempotency_key
    )
    db.add(ledger)
    customer.loyalty_points += payload.points_delta

    db.commit()
    db.refresh(ledger)
    return ledger


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_staff)
):
    """
    Delete or deactivate a restaurant customer safely.
    """
    customer = db.query(RestaurantCustomer).filter(RestaurantCustomer.id == customer_id).first()
    if customer:
        db.delete(customer)
        db.commit()
    return None


@router.patch("/customers/{customer_id}", response_model=RestaurantCustomerResponse)
def update_customer_profile(
    customer_id: UUID,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_staff)
):
    """
    Update customer profile details.
    """
    customer = db.query(RestaurantCustomer).filter(RestaurantCustomer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if "name" in payload and payload["name"]:
        customer.name = payload["name"]
    if "phone" in payload and payload["phone"]:
        customer.phone = payload["phone"]
    if "email" in payload:
        customer.email = payload["email"]
    if "notes" in payload:
        customer.notes = payload["notes"]
    if "is_active" in payload and payload["is_active"] is not None:
        customer.is_active = payload["is_active"]

    db.commit()
    db.refresh(customer)
    return customer
