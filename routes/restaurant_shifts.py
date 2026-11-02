from typing import Optional
from uuid import UUID
import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.user import User
from models.restaurant_shift import RestaurantShift
from models.restaurant_order import RestaurantOrder
from models.restaurant_tender import RestaurantTender
from schemas.restaurant_shift import RestaurantShiftOpen, RestaurantShiftClose, RestaurantShiftResponse
from dependencies import get_restaurant_cashier

router = APIRouter(
    prefix="/api/restaurant/shifts",
    tags=["Restaurant - Shifts"]
)

@router.post("/open", response_model=RestaurantShiftResponse, status_code=status.HTTP_201_CREATED)
def open_shift(
    payload: RestaurantShiftOpen,
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Open cashier shift with opening cash float.
    """
    active_shift = (
        db.query(RestaurantShift)
        .filter(RestaurantShift.cashier_id == cashier_user.id)
        .filter(RestaurantShift.status == "OPEN")
        .first()
    )
    if active_shift:
        raise HTTPException(status_code=400, detail="You already have an open shift")

    tenant_id = cashier_user.tenant_id
    shift = RestaurantShift(
        outlet_id=payload.outlet_id,
        tenant_id=tenant_id or uuid.uuid4(),
        cashier_id=cashier_user.id,
        status="OPEN",
        opened_at=datetime.utcnow(),
        opening_cash=payload.opening_cash,
        notes=payload.notes
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.post("/{shift_id}/close", response_model=RestaurantShiftResponse)
def close_shift(
    shift_id: UUID,
    payload: RestaurantShiftClose,
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Close cashier shift, calculate expected cash from cash tenders and compute variance.
    """
    shift = db.query(RestaurantShift).filter(RestaurantShift.id == shift_id).first()
    if not shift or shift.status != "OPEN":
        raise HTTPException(status_code=404, detail="Active shift not found")

    # Sum up all CASH tenders collected during this shift
    cash_collected = (
        db.query(func.coalesce(func.sum(RestaurantTender.amount), 0))
        .join(RestaurantOrder, RestaurantTender.order_id == RestaurantOrder.id)
        .filter(RestaurantOrder.shift_id == shift.id)
        .filter(RestaurantTender.method == "CASH")
        .scalar()
    )

    expected = Decimal(str(shift.opening_cash)) + Decimal(str(cash_collected))
    variance = Decimal(str(payload.counted_cash)) - expected

    shift.status = "CLOSED"
    shift.closed_at = datetime.utcnow()
    shift.counted_cash = payload.counted_cash
    shift.expected_cash = expected
    shift.variance = variance
    if payload.notes:
        shift.notes = (shift.notes or "") + " | Close: " + payload.notes

    db.commit()
    db.refresh(shift)
    return shift


@router.get("/active", response_model=Optional[RestaurantShiftResponse])
def get_active_shift(
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Get current open shift for the authenticated cashier.
    """
    return (
        db.query(RestaurantShift)
        .filter(RestaurantShift.cashier_id == cashier_user.id)
        .filter(RestaurantShift.status == "OPEN")
        .first()
    )


@router.get("/{shift_id}/summary")
def get_shift_summary(
    shift_id: UUID,
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Detailed breakdown of tenders, sales, and variances for a specific shift.
    """
    shift = db.query(RestaurantShift).filter(RestaurantShift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    tender_breakdown = (
        db.query(
            RestaurantTender.method,
            func.coalesce(func.sum(RestaurantTender.amount), 0).label("total_amount"),
            func.count(RestaurantTender.id).label("count")
        )
        .join(RestaurantOrder, RestaurantTender.order_id == RestaurantOrder.id)
        .filter(RestaurantOrder.shift_id == shift.id)
        .filter(RestaurantTender.status == "COMPLETED")
        .group_by(RestaurantTender.method)
        .all()
    )

    tenders_data = [
        {"method": t.method, "amount": float(t.total_amount), "count": t.count}
        for t in tender_breakdown
    ]

    return {
        "shift_id": str(shift.id),
        "status": shift.status,
        "cashier_id": str(shift.cashier_id),
        "opened_at": shift.opened_at.isoformat() if shift.opened_at else None,
        "closed_at": shift.closed_at.isoformat() if shift.closed_at else None,
        "opening_cash": float(shift.opening_cash),
        "counted_cash": float(shift.counted_cash) if shift.counted_cash is not None else None,
        "expected_cash": float(shift.expected_cash) if shift.expected_cash is not None else None,
        "variance": float(shift.variance) if shift.variance is not None else None,
        "tenders": tenders_data,
        "notes": shift.notes
    }

