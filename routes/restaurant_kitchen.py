from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from models.database import get_db
from models.user import User
from models.restaurant_order import RestaurantOrder
from models.restaurant_kitchen import RestaurantKitchenTicket, RestaurantKitchenTicketItem, RestaurantKitchenEvent
from models.restaurant_audit import RestaurantAuditEvent
from schemas.restaurant_kitchen import KitchenTicketResponse, KitchenTicketItemResponse, KitchenEventCreate
from dependencies import get_restaurant_kitchen, get_restaurant_staff


router = APIRouter(
    prefix="/api/restaurant/kitchen",
    tags=["Restaurant - Kitchen / KDS"]
)

@router.get("/tickets", response_model=List[KitchenTicketResponse])
def get_kitchen_tickets(
    outlet_id: UUID,
    station: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_kitchen)
):
    """
    List KOT tickets for Kitchen Display System (KDS).
    """
    query = (
        db.query(RestaurantKitchenTicket)
        .join(RestaurantOrder, RestaurantKitchenTicket.order_id == RestaurantOrder.id)
        .options(joinedload(RestaurantKitchenTicket.items))
        .filter(RestaurantOrder.outlet_id == outlet_id)
    )
    if station:
        query = query.filter(RestaurantKitchenTicket.station == station)
    if status_filter:
        query = query.filter(RestaurantKitchenTicket.status == status_filter)
    else:
        # By default exclude served/cancelled tickets
        query = query.filter(RestaurantKitchenTicket.status.in_(["PENDING", "PREPARING", "READY"]))

    return query.order_by(RestaurantKitchenTicket.created_at.asc()).all()


@router.post("/tickets/{ticket_id}/events", response_model=KitchenTicketResponse)
def log_ticket_event(
    ticket_id: UUID,
    payload: KitchenEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_kitchen)
):
    """
    Update ticket status (e.g. PREPARING -> READY -> SERVED) on KDS.
    """
    ticket = db.query(RestaurantKitchenTicket).filter(RestaurantKitchenTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Kitchen ticket not found")

    old_status = ticket.status
    ticket.status = payload.to_status
    if payload.to_status in ["READY", "SERVED"]:
        ticket.completed_at = datetime.utcnow()

    # Log transition event
    event = RestaurantKitchenEvent(
        ticket_id=ticket.id,
        actor_id=current_user.id,
        from_status=old_status,
        to_status=payload.to_status,
        notes=payload.notes
    )
    db.add(event)

    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/tickets/{ticket_id}/reprint", response_model=KitchenTicketResponse)
def reprint_kot(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_staff)
):
    """
    Audit-logged KOT ticket reprint without modifying order financial totals.
    """
    ticket = db.query(RestaurantKitchenTicket).filter(RestaurantKitchenTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Kitchen ticket not found")

    ticket.is_reprint = True
    ticket.reprint_count += 1

    # Log audit event
    order = db.query(RestaurantOrder).filter(RestaurantOrder.id == ticket.order_id).first()
    if order:
        audit = RestaurantAuditEvent(
            outlet_id=order.outlet_id,
            tenant_id=order.tenant_id,
            actor_id=current_user.id,
            action="KOT_REPRINT",
            entity_name="kitchen_ticket",
            entity_id=str(ticket.id),
            reason=f"Reprint #{ticket.reprint_count}"
        )
        db.add(audit)

    db.commit()
    db.refresh(ticket)
    return ticket


from schemas.restaurant_kitchen import KitchenEventResponse, KitchenItemStatusUpdate, CancelKitchenTicket
from models.restaurant_order_line import RestaurantOrderLine
from dependencies import get_restaurant_manager

@router.get("/tickets/{ticket_id}/events", response_model=List[KitchenEventResponse])
def get_ticket_event_history(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_kitchen)
):
    """
    Get audit history of all state changes for a given kitchen ticket.
    """
    ticket = db.query(RestaurantKitchenTicket).filter(RestaurantKitchenTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Kitchen ticket not found")

    return (
        db.query(RestaurantKitchenEvent)
        .filter(RestaurantKitchenEvent.ticket_id == ticket_id)
        .order_by(RestaurantKitchenEvent.created_at.asc())
        .all()
    )


@router.patch("/tickets/items/{ticket_item_id}/status", response_model=KitchenTicketItemResponse)
def update_ticket_item_status(
    ticket_item_id: UUID,
    payload: KitchenItemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_kitchen)
):
    """
    Allows a kitchen cook to advance a single item's status (e.g. PREPARING -> READY).
    Reflects back to the parent order line status.
    """
    item = db.query(RestaurantKitchenTicketItem).filter(RestaurantKitchenTicketItem.id == ticket_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ticket item not found")

    item.status = payload.status

    # Mirror status to original order line
    order_line = db.query(RestaurantOrderLine).filter(RestaurantOrderLine.id == item.order_line_id).first()
    if order_line:
        order_line.kot_status = payload.status

    db.commit()
    db.refresh(item)
    return item


@router.post("/tickets/{ticket_id}/cancel", response_model=KitchenTicketResponse)
def cancel_kitchen_ticket(
    ticket_id: UUID,
    payload: CancelKitchenTicket,
    db: Session = Depends(get_db),
    manager_user: User = Depends(get_restaurant_manager)
):
    """
    Cancel an entire KOT ticket (Manager authorization required).
    Logs an audit event and marks order lines as CANCELLED.
    """
    ticket = db.query(RestaurantKitchenTicket).filter(RestaurantKitchenTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Kitchen ticket not found")

    if ticket.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Ticket is already cancelled")

    old_status = ticket.status
    ticket.status = "CANCELLED"

    for itm in ticket.items:
        itm.status = "CANCELLED"
        order_line = db.query(RestaurantOrderLine).filter(RestaurantOrderLine.id == itm.order_line_id).first()
        if order_line:
            order_line.kot_status = "CANCELLED"

    # Kitchen event
    k_event = RestaurantKitchenEvent(
        ticket_id=ticket.id,
        actor_id=manager_user.id,
        from_status=old_status,
        to_status="CANCELLED",
        notes=f"Cancelled by manager: {payload.reason}"
    )
    db.add(k_event)

    # General restaurant audit event
    order = db.query(RestaurantOrder).filter(RestaurantOrder.id == ticket.order_id).first()
    if order:
        audit = RestaurantAuditEvent(
            outlet_id=order.outlet_id,
            tenant_id=order.tenant_id,
            actor_id=manager_user.id,
            action="KOT_CANCELLED",
            entity_name="kitchen_ticket",
            entity_id=str(ticket.id),
            reason=payload.reason,
            before_state={"status": old_status},
            after_state={"status": "CANCELLED"}
        )
        db.add(audit)

    db.commit()
    db.refresh(ticket)
    return ticket


from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from models.restaurant_table import RestaurantTable

kot_template_env = Environment(loader=FileSystemLoader(searchpath="./templates"))

@router.get("/tickets/{ticket_id}/thermal-kot", response_class=HTMLResponse)
def render_thermal_kot(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_staff)
):
    """
    Renders 80mm thermal Kitchen Order Ticket (KOT) HTML.
    Highlights station, table number, quantities, modifier instructions, and reprint banner.
    """
    ticket = (
        db.query(RestaurantKitchenTicket)
        .options(joinedload(RestaurantKitchenTicket.items))
        .filter(RestaurantKitchenTicket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Kitchen ticket not found")

    order = db.query(RestaurantOrder).filter(RestaurantOrder.id == ticket.order_id).first()
    table = db.query(RestaurantTable).filter(RestaurantTable.id == order.table_id).first() if order and order.table_id else None
    server_user = db.query(User).filter(User.id == ticket.server_user_id).first() if ticket.server_user_id else None

    order_data = {
        "order_number": order.order_number if order else "N/A",
        "order_type": order.order_type if order else "DINE_IN",
        "table_code": table.table_code if table else None,
        "notes": order.notes if order else None
    }

    template = kot_template_env.get_template("kot_bill_template.html")
    html_out = template.render(
        ticket=ticket,
        order=order_data,
        server_name=server_user.name if server_user else None
    )

    return HTMLResponse(content=html_out)


