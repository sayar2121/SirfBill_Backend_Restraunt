from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import User
from models.restaurant_outlet import RestaurantOutlet
from models.restaurant_table import RestaurantTable
from models.restaurant_order import RestaurantOrder
from schemas.restaurant_table import RestaurantTableCreate, RestaurantTableUpdate, RestaurantTableResponse
from dependencies import get_restaurant_staff, get_restaurant_manager, get_optional_restaurant_staff

router = APIRouter(
    prefix="/api/restaurant/tables",
    tags=["Restaurant - Tables"]
)

@router.get("", response_model=List[RestaurantTableResponse])
def get_tables(
    outlet_id: Optional[UUID] = None,
    section: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    """
    List tables with live status (VACANT, OCCUPIED, RESERVED, CLEANING).
    Automatically maps active orders with their start time and amounts.
    """
    if not outlet_id:
        first_outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.is_active == True).first()
        if not first_outlet:
            return []
        outlet_id = first_outlet.id

    query = (
        db.query(RestaurantTable)
        .filter(RestaurantTable.outlet_id == outlet_id)
        .filter(RestaurantTable.is_active == True)
    )
    if section:
        query = query.filter(RestaurantTable.section == section)
    if status_filter:
        query = query.filter(RestaurantTable.status == status_filter)
    tables = query.order_by(RestaurantTable.table_code.asc()).all()
    if not tables:
        return []

    # Map active orders for occupied tables (including OPEN, SENT_TO_KITCHEN, HOLD, SERVED awaiting settlement)
    active_orders = (
        db.query(RestaurantOrder)
        .filter(RestaurantOrder.outlet_id == outlet_id)
        .filter(RestaurantOrder.table_id.isnot(None))
        .filter(RestaurantOrder.status.in_(["OPEN", "SENT_TO_KITCHEN", "HOLD", "SERVED"]))
        .order_by(RestaurantOrder.created_at.asc())
        .all()
    )
    table_order_map = {o.table_id: o for o in active_orders}

    result = []
    for t in tables:
        t_resp = RestaurantTableResponse.model_validate(t)
        t_resp.table_number = t.table_code
        t_resp.floor = t.section
        active_o = table_order_map.get(t.id)
        if active_o:
            t_resp.status = "OCCUPIED"
            t_resp.active_order_id = active_o.id
            t_resp.active_order_number = active_o.order_number
            t_resp.active_order_status = active_o.status
            t_resp.active_order_created_at = active_o.created_at
            t_resp.active_order_grand_total = float(active_o.grand_total or 0.0)
        else:
            if t.status == "OCCUPIED":
                # No active order remaining for this table -> table is automatically VACANT
                t.status = "VACANT"
                db.commit()
                t_resp.status = "VACANT"
        result.append(t_resp)
    return result

@router.post("", response_model=RestaurantTableResponse, status_code=status.HTTP_201_CREATED)
def create_table(
    payload: RestaurantTableCreate,
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    # Auto-resolve outlet_id if not provided
    outlet = None
    if payload.outlet_id:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == payload.outlet_id).first()
    if not outlet:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.is_active == True).first()
    if not outlet:
        outlet = db.query(RestaurantOutlet).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="No active restaurant outlet found to attach table to.")

    table_name = payload.table_number or payload.table_code or "T1"
    floor_name = payload.floor or payload.section or "Floor 1"
    table_status = (payload.status or "VACANT").upper()
    if table_status == "AVAILABLE":
        table_status = "VACANT"

    table = RestaurantTable(
        outlet_id=outlet.id,
        tenant_id=outlet.tenant_id,
        table_code=table_name,
        section=floor_name,
        capacity=payload.capacity,
        status=table_status,
        is_active=payload.is_active
    )
    db.add(table)
    db.commit()
    db.refresh(table)

    resp = RestaurantTableResponse.model_validate(table)
    resp.table_number = table.table_code
    resp.floor = table.section
    return resp

@router.put("/{table_id}", response_model=RestaurantTableResponse)
@router.patch("/{table_id}", response_model=RestaurantTableResponse)
def update_table(
    table_id: UUID,
    payload: RestaurantTableUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    table = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    if payload.table_number:
        table.table_code = payload.table_number
    elif payload.table_code:
        table.table_code = payload.table_code

    if payload.floor:
        table.section = payload.floor
    elif payload.section:
        table.section = payload.section

    if payload.capacity is not None:
        table.capacity = payload.capacity

    if payload.status:
        st = payload.status.upper()
        if st in ["AVAILABLE", "VACANT", "CLEAN"]:
            st = "VACANT"
            # Cancel/clear any active order still lingering on this table
            active_orders = (
                db.query(RestaurantOrder)
                .filter(RestaurantOrder.table_id == table_id)
                .filter(RestaurantOrder.status.in_(["OPEN", "SENT_TO_KITCHEN", "HOLD", "SERVED"]))
                .all()
            )
            for act_ord in active_orders:
                act_ord.status = "CANCELLED"
                act_ord.version += 1
        table.status = st

    if payload.is_active is not None:
        table.is_active = payload.is_active

    db.commit()
    db.refresh(table)

    resp = RestaurantTableResponse.model_validate(table)
    resp.table_number = table.table_code
    resp.floor = table.section
    return resp

@router.patch("/{table_id}/status", response_model=RestaurantTableResponse)
@router.put("/{table_id}/status", response_model=RestaurantTableResponse)
def update_table_status(
    table_id: UUID,
    payload: RestaurantTableUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    table = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    if payload.status:
        st = payload.status.upper()
        if st in ["AVAILABLE", "VACANT", "CLEAN"]:
            st = "VACANT"
            # Cancel/clear any active order still lingering on this table
            active_orders = (
                db.query(RestaurantOrder)
                .filter(RestaurantOrder.table_id == table_id)
                .filter(RestaurantOrder.status.in_(["OPEN", "SENT_TO_KITCHEN", "HOLD", "SERVED"]))
                .all()
            )
            for act_ord in active_orders:
                act_ord.status = "CANCELLED"
                act_ord.version += 1
        table.status = st

    db.commit()
    db.refresh(table)

    resp = RestaurantTableResponse.model_validate(table)
    resp.table_number = table.table_code
    resp.floor = table.section
    return resp

@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_table(
    table_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    table = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if table:
        db.delete(table)
        db.commit()
    return None

from schemas.restaurant_order import RestaurantOpenTableOrder, RestaurantOrderResponse
from models.restaurant_order import RestaurantOrder

@router.post("/{table_id}/open-order", response_model=RestaurantOrderResponse, status_code=status.HTTP_201_CREATED)
def open_table_order(
    table_id: UUID,
    payload: RestaurantOpenTableOrder,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_staff)
):
    """
    Opens or resumes an active dine-in order for a specific table.
    Ensures no conflicting open orders exist on the same table.
    """
    table = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    # Check for existing open order on this table
    existing_order = (
        db.query(RestaurantOrder)
        .filter(RestaurantOrder.table_id == table_id)
        .filter(RestaurantOrder.status.in_(["OPEN", "SENT_TO_KITCHEN", "HOLD", "SERVED"]))
        .first()
    )
    if existing_order:
        if payload.customer_name and payload.customer_name != "Walk-in Guest":
            existing_order.customer_name = payload.customer_name
        if payload.customer_phone:
            existing_order.customer_phone = payload.customer_phone
        if payload.notes:
            existing_order.notes = payload.notes
        db.commit()
        db.refresh(existing_order)
        return existing_order

    # Generate sequential order number
    from datetime import datetime
    today_str = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"ORD-{today_str}-"
    count = (
        db.query(RestaurantOrder)
        .filter(RestaurantOrder.outlet_id == table.outlet_id)
        .filter(RestaurantOrder.order_number.like(f"{prefix}%"))
        .count()
    )
    order_num = f"{prefix}{count + 1:04d}"

    order = RestaurantOrder(
        outlet_id=table.outlet_id,
        tenant_id=table.tenant_id,
        order_number=order_num,
        order_type="DINE_IN",
        status="OPEN",
        table_id=table.id,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        waiter_id=current_user.id,
        notes=payload.notes,
        idempotency_key=payload.idempotency_key,
        version=1
    )
    db.add(order)
    table.status = "OCCUPIED"

    db.commit()
    db.refresh(order)
    return order

