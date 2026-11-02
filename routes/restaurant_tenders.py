from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import User
from models.restaurant_order import RestaurantOrder
from models.restaurant_table import RestaurantTable
from models.restaurant_tender import RestaurantTender, RestaurantRefund
from models.restaurant_audit import RestaurantAuditEvent
from schemas.restaurant_tender import (
    RestaurantTenderCreate, RestaurantTenderResponse,
    RestaurantRefundCreate, RestaurantRefundResponse
)
from dependencies import get_restaurant_cashier, get_restaurant_manager

router = APIRouter(
    prefix="/api/restaurant/orders",
    tags=["Restaurant - Tenders & Refunds"]
)

@router.post("/{order_id}/tenders", response_model=RestaurantTenderResponse, status_code=status.HTTP_201_CREATED)
def add_tender(
    order_id: UUID,
    payload: RestaurantTenderCreate,
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Post settlement tender (Cash, UPI, Card). Supports mixed/split tender.
    Idempotent and guarantees atomic financial status updates.
    """
    # 1. Idempotency check
    if payload.idempotency_key:
        existing = (
            db.query(RestaurantTender)
            .filter(RestaurantTender.idempotency_key == payload.idempotency_key)
            .first()
        )
        if existing:
            return existing

    order = db.query(RestaurantOrder).filter(RestaurantOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    amount = Decimal(str(payload.amount))
    balance_due = order.grand_total - order.paid_amount

    tender = RestaurantTender(
        order_id=order.id,
        tenant_id=order.tenant_id,
        method=payload.method.upper(),
        amount=amount,
        reference=payload.reference,
        status="COMPLETED",
        cashier_id=cashier_user.id,
        idempotency_key=payload.idempotency_key
    )
    db.add(tender)

    order.paid_amount += amount
    if order.paid_amount >= order.grand_total:
        order.status = "COMPLETED"
        if order.table_id:
            table = db.query(RestaurantTable).filter(RestaurantTable.id == order.table_id).first()
            if table:
                table.status = "CLEANING" # Marked for cleaning after payment

    order.version += 1
    db.commit()
    db.refresh(tender)
    return tender


@router.post("/{order_id}/refunds", response_model=RestaurantRefundResponse, status_code=status.HTTP_201_CREATED)
def refund_tender(
    order_id: UUID,
    payload: RestaurantRefundCreate,
    db: Session = Depends(get_db),
    manager_user: User = Depends(get_restaurant_manager)
):
    """
    Issue refund against a tender. Requires Manager/Owner permission.
    """
    tender = db.query(RestaurantTender).filter(RestaurantTender.id == payload.tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    refund_amount = Decimal(str(payload.amount))
    if refund_amount > tender.amount:
        raise HTTPException(status_code=400, detail="Refund amount exceeds tender amount")

    refund = RestaurantRefund(
        tender_id=tender.id,
        order_id=order_id,
        amount=refund_amount,
        reason=payload.reason,
        authorized_by=manager_user.id
    )
    db.add(refund)

    # Adjust order paid amount
    order = db.query(RestaurantOrder).filter(RestaurantOrder.id == order_id).first()
    if order:
        order.paid_amount -= refund_amount
        order.version += 1

        # Audit Event
        audit = RestaurantAuditEvent(
            outlet_id=order.outlet_id,
            tenant_id=order.tenant_id,
            actor_id=manager_user.id,
            action="TENDER_REFUND",
            entity_name="tender",
            entity_id=str(tender.id),
            reason=payload.reason,
            after_state={"refund_amount": float(refund_amount)}
        )
        db.add(audit)

    db.commit()
    db.refresh(refund)
    return refund


from schemas.restaurant_tender import (
    RestaurantMultiTenderCheckout, RestaurantReceiptResponse, ReceiptLineItem
)
from models.restaurant_outlet import RestaurantOutlet

@router.get("/{order_id}/tenders", response_model=List[RestaurantTenderResponse])
def get_order_tenders(
    order_id: UUID,
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Get all tender settlements for an order.
    """
    return (
        db.query(RestaurantTender)
        .filter(RestaurantTender.order_id == order_id)
        .order_by(RestaurantTender.created_at.asc())
        .all()
    )


@router.post("/{order_id}/checkout-split", response_model=List[RestaurantTenderResponse], status_code=status.HTTP_201_CREATED)
@router.post("/{order_id}/settle", response_model=List[RestaurantTenderResponse], status_code=status.HTTP_201_CREATED)
def checkout_split_tenders(
    order_id: UUID,
    payload: RestaurantMultiTenderCheckout,
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Mixed / Split Tender checkout / settlement in a single atomic database transaction.
    Enforces that sum(tenders) satisfies order balance due.
    """
    order = db.query(RestaurantOrder).filter(RestaurantOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Order is already completed/paid")

    # Apply inline discount if provided
    if payload.discount_type and payload.discount_value and payload.discount_value > 0:
        disc_val = Decimal(str(payload.discount_value))
        if payload.discount_type == "PERCENTAGE":
            disc_amount = (order.subtotal * (disc_val / Decimal("100"))).quantize(Decimal("0.01"))
        else:
            disc_amount = disc_val

        order.discount_amount = min(order.subtotal, disc_amount)
        order.discount_reason = payload.discount_reason or "POS Settle Discount"
        
        from decimal import ROUND_HALF_UP
        raw_total = order.subtotal - order.discount_amount + order.tax_amount
        rounded_grand = raw_total.quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)
        order.rounding_adjustment = rounded_grand - raw_total
        order.grand_total = rounded_grand

    tender_list = payload.tenders or payload.payment_splits or []
    if not tender_list:
        raise HTTPException(status_code=400, detail="No payment tenders or payment_splits provided")

    balance_due = order.grand_total - order.paid_amount
    total_tendered = sum(Decimal(str(t.amount)) for t in tender_list)

    if total_tendered < balance_due:
        raise HTTPException(
            status_code=400,
            detail=f"Total tendered amount ({total_tendered}) is less than balance due ({balance_due})"
        )

    # Attach to active cashier shift if open
    from models.restaurant_shift import RestaurantShift
    active_shift = (
        db.query(RestaurantShift)
        .filter(RestaurantShift.cashier_id == cashier_user.id)
        .filter(RestaurantShift.status == "OPEN")
        .first()
    )
    if active_shift:
        order.shift_id = active_shift.id

    created_tenders = []
    for t_item in tender_list:
        tender = RestaurantTender(
            order_id=order.id,
            tenant_id=order.tenant_id,
            method=t_item.method.upper(),
            amount=Decimal(str(t_item.amount)),
            reference=t_item.reference,
            status="COMPLETED",
            cashier_id=cashier_user.id,
            idempotency_key=f"{payload.idempotency_key}_{t_item.method}" if payload.idempotency_key else None
        )
        db.add(tender)
        created_tenders.append(tender)

    order.paid_amount += total_tendered
    order.status = "COMPLETED"
    order.version += 1

    if order.table_id:
        table = db.query(RestaurantTable).filter(RestaurantTable.id == order.table_id).first()
        if table:
            table.status = "CLEANING"

    db.commit()
    for t in created_tenders:
        db.refresh(t)
    return created_tenders


@router.get("/{order_id}/receipt", response_model=RestaurantReceiptResponse)
def get_order_receipt(
    order_id: UUID,
    is_reprint: bool = False,
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Generate clean, printable restaurant invoice / receipt data.
    Audits reprints without modifying financials.
    """
    order = db.query(RestaurantOrder).filter(RestaurantOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == order.outlet_id).first()
    table = db.query(RestaurantTable).filter(RestaurantTable.id == order.table_id).first() if order.table_id else None

    # Track receipt reprint in audit log
    reprint_count = 0
    if is_reprint:
        audit_count = (
            db.query(RestaurantAuditEvent)
            .filter(RestaurantAuditEvent.entity_id == str(order.id))
            .filter(RestaurantAuditEvent.action == "RECEIPT_REPRINT")
            .count()
        )
        reprint_count = audit_count + 1
        audit = RestaurantAuditEvent(
            outlet_id=order.outlet_id,
            tenant_id=order.tenant_id,
            actor_id=cashier_user.id,
            action="RECEIPT_REPRINT",
            entity_name="order_receipt",
            entity_id=str(order.id),
            reason=f"Receipt Reprint #{reprint_count}"
        )
        db.add(audit)
        db.commit()

    line_items = []
    for line in order.lines:
        mods_str = ", ".join([m["name"] for m in line.selected_modifiers]) if line.selected_modifiers else None
        line_items.append(ReceiptLineItem(
            name=line.item_name,
            variant=line.variant_name,
            quantity=line.quantity,
            unit_price=line.unit_price + line.modifier_price,
            line_total=line.line_total,
            modifiers=mods_str
        ))

    tenders = (
        db.query(RestaurantTender)
        .filter(RestaurantTender.order_id == order.id)
        .all()
    )

    change_due = max(Decimal("0.00"), order.paid_amount - order.grand_total)

    return RestaurantReceiptResponse(
        order_id=order.id,
        order_number=order.order_number,
        order_type=order.order_type,
        outlet_name=outlet.name if outlet else "Restaurant",
        table_code=table.table_code if table else None,
        cashier_name=cashier_user.name,
        date=order.created_at,
        items=line_items,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        tax_amount=order.tax_amount,
        rounding_adjustment=order.rounding_adjustment,
        grand_total=order.grand_total,
        paid_amount=order.paid_amount,
        change_due=change_due,
        tenders=tenders,
        is_reprint=is_reprint,
        reprint_count=reprint_count
    )


from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from models.shop_settings import ShopSettings
from models.restaurant_kitchen import RestaurantKitchenTicket
from utils.upi_qr import generate_upi_qr_url

# Initialize Jinja2 environment for thermal printing
thermal_template_env = Environment(loader=FileSystemLoader(searchpath="./templates"))

@router.get("/{order_id}/thermal-bill", response_class=HTMLResponse)
@router.post("/{order_id}/print-bill", response_class=HTMLResponse)
@router.get("/{order_id}/print-bill", response_class=HTMLResponse)
def render_thermal_bill(
    order_id: UUID,
    is_reprint: bool = False,
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Renders 80mm thermal receipt HTML with logo, header, table, GST breakup,
    dynamic amount-based UPI QR, already-paid badge, and 'Powered by SirfBill'.
    """
    order = db.query(RestaurantOrder).filter(RestaurantOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == order.outlet_id).first()
    table = db.query(RestaurantTable).filter(RestaurantTable.id == order.table_id).first() if order.table_id else None

    # Load shop settings for logo, GST, address, and UPI ID
    shop_settings = None
    if outlet and outlet.shop_id:
        shop_settings = db.query(ShopSettings).filter(ShopSettings.shop_id == outlet.shop_id).first()
    if not shop_settings:
        shop_settings = db.query(ShopSettings).first()

    # Determine latest KOT ticket number if available
    latest_kot = (
        db.query(RestaurantKitchenTicket)
        .filter(RestaurantKitchenTicket.order_id == order.id)
        .order_by(RestaurantKitchenTicket.created_at.desc())
        .first()
    )

    # Calculate financial balance
    balance_due = max(Decimal("0.00"), order.grand_total - order.paid_amount)
    is_paid = (order.paid_amount >= order.grand_total and order.grand_total > 0) or order.status == "COMPLETED"

    # Fetch tenders
    tenders = (
        db.query(RestaurantTender)
        .filter(RestaurantTender.order_id == order.id)
        .all()
    )
    primary_payment_mode = ", ".join([t.method for t in tenders]) if tenders else None

    # Generate Dynamic UPI QR for unpaid balance
    upi_id = (outlet.service_settings or {}).get("upi_id") or (shop_settings.upi_id if shop_settings else None)
    upi_qr_url = ""
    if not is_paid and balance_due > 0 and upi_id:
        payee_name = outlet.name or (shop_settings.shop_name if shop_settings else "Restaurant")
        note = f"Bill {order.order_number}"
        upi_qr_url = generate_upi_qr_url(
            upi_id=upi_id,
            payee_name=payee_name,
            amount=balance_due,
            transaction_note=note
        )

    # Process order lines with modifier summaries and consolidate identical items
    consolidated_dict = {}
    for line in order.lines:
        mods_str = ", ".join([m["name"] for m in line.selected_modifiers]) if line.selected_modifiers else None
        eff_unit_price = float(line.unit_price + line.modifier_price)
        base_line_total = eff_unit_price * int(line.quantity)
        key = (line.item_name, line.variant_name or "Standard", eff_unit_price, mods_str or "")
        if key in consolidated_dict:
            consolidated_dict[key]["quantity"] += int(line.quantity)
            consolidated_dict[key]["line_total"] += base_line_total
        else:
            consolidated_dict[key] = {
                "item_name": line.item_name,
                "variant_name": line.variant_name,
                "quantity": int(line.quantity),
                "unit_price": eff_unit_price,
                "line_total": base_line_total,
                "modifiers": mods_str
            }
    formatted_lines = list(consolidated_dict.values())

    # Prepare Outlet Details
    outlet_data = {
        "name": outlet.name if outlet else (shop_settings.shop_name if shop_settings else "Restaurant"),
        "address": (shop_settings.address if shop_settings else None) or (outlet.service_settings or {}).get("address", ""),
        "phone": (shop_settings.phone if shop_settings else None) or (outlet.service_settings or {}).get("phone", ""),
        "gst_number": (shop_settings.gst_number if shop_settings else None) or (outlet.service_settings or {}).get("gst_number", ""),
        "logo_url": (outlet.logo_url if outlet and outlet.logo_url else None) or (shop_settings.logo_url if shop_settings and shop_settings.logo_url else (outlet.service_settings or {}).get("logo_url"))
    }

    change_due = max(Decimal("0.00"), order.paid_amount - order.grand_total)

    order_data = {
        "order_number": order.order_number,
        "order_type": order.order_type,
        "table_code": table.table_code if table else None,
        "customer_name": order.customer_name or "Walk-in Guest",
        "customer_phone": order.customer_phone or "",
        "created_at": order.created_at,
        "kot_number": latest_kot.ticket_number if latest_kot else None,
        "lines": formatted_lines,
        "subtotal": float(order.subtotal),
        "discount_amount": float(order.discount_amount),
        "discount_reason": order.discount_reason,
        "tax_amount": float(order.tax_amount),
        "rounding_adjustment": float(order.rounding_adjustment),
        "grand_total": float(order.grand_total),
        "paid_amount": float(order.paid_amount),
        "change_due": float(change_due),
        "tenders": [{"method": t.method, "amount": float(t.amount)} for t in tenders]
    }

    template = thermal_template_env.get_template("thermal_bill_template.html")
    html_content = template.render(
        outlet=outlet_data,
        order=order_data,
        cashier_name=cashier_user.name,
        is_paid=is_paid,
        balance_due=float(balance_due),
        primary_payment_mode=primary_payment_mode,
        upi_qr_url=upi_qr_url
    )

    return HTMLResponse(content=html_content)


from pydantic import BaseModel

class DynamicUpiQrRequest(BaseModel):
    order_id: UUID
    amount: Optional[Decimal] = None
    table_number: Optional[str] = None

@router.post("/payments/generate-upi-qr")
def generate_dynamic_upi_qr(
    payload: DynamicUpiQrRequest,
    db: Session = Depends(get_db),
    cashier_user: User = Depends(get_restaurant_cashier)
):
    """
    Generate dynamic UPI QR link and base64/url for live POS payments.
    """
    order = db.query(RestaurantOrder).filter(RestaurantOrder.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == order.outlet_id).first()
    shop_settings = None
    if outlet and outlet.shop_id:
        shop_settings = db.query(ShopSettings).filter(ShopSettings.shop_id == outlet.shop_id).first()
    if not shop_settings:
        shop_settings = db.query(ShopSettings).first()

    upi_id = (outlet.service_settings or {}).get("upi_id") or (shop_settings.upi_id if shop_settings else None)
    if not upi_id:
        raise HTTPException(status_code=400, detail="No UPI ID configured for this outlet or shop settings")

    amt = payload.amount or max(Decimal("0.00"), order.grand_total - order.paid_amount)
    payee_name = outlet.name if outlet else (shop_settings.shop_name if shop_settings else "Restaurant")
    note = f"Bill {order.order_number}"
    deep_link = f"upi://pay?pa={upi_id}&pn={payee_name}&am={amt}&tr={order.id}&tn={note}&cu=INR"
    qr_url = generate_upi_qr_url(upi_id=upi_id, payee_name=payee_name, amount=amt, transaction_note=note)

    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "amount": float(amt),
        "upi_id": upi_id,
        "payee_name": payee_name,
        "upi_deep_link": deep_link,
        "qr_image_url": qr_url
    }


