from typing import Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.user import User
from models.restaurant_order import RestaurantOrder
from models.restaurant_tender import RestaurantTender
from schemas.restaurant_reports import DailySalesReportResponse, SalesSummaryReport, TenderSummaryItem
from dependencies import get_restaurant_manager

router = APIRouter(
    prefix="/api/restaurant/reports",
    tags=["Restaurant - Reports & Analytics"]
)

@router.get("/sales", response_model=DailySalesReportResponse)
def get_daily_sales_report(
    outlet_id: UUID,
    report_date: Optional[date] = None,
    db: Session = Depends(get_db),
    manager_user: User = Depends(get_restaurant_manager)
):
    """
    Generate sales report by order type, taxes, discounts, and tender breakdown.
    """
    target_date = report_date or date.today()
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())

    orders_query = (
        db.query(RestaurantOrder)
        .filter(RestaurantOrder.outlet_id == outlet_id)
        .filter(RestaurantOrder.created_at >= start_dt)
        .filter(RestaurantOrder.created_at <= end_dt)
        .filter(RestaurantOrder.status.in_(["OPEN", "SENT_TO_KITCHEN", "COMPLETED"]))
    )

    orders = orders_query.all()

    total_sales = Decimal("0.00")
    dine_in_sales = Decimal("0.00")
    takeaway_sales = Decimal("0.00")
    delivery_sales = Decimal("0.00")
    total_tax = Decimal("0.00")
    total_discount = Decimal("0.00")

    for o in orders:
        total_sales += o.grand_total
        total_tax += o.tax_amount
        total_discount += o.discount_amount
        if o.order_type == "DINE_IN":
            dine_in_sales += o.grand_total
        elif o.order_type == "TAKEAWAY":
            takeaway_sales += o.grand_total
        elif o.order_type == "DELIVERY":
            delivery_sales += o.grand_total

    summary = SalesSummaryReport(
        total_sales=total_sales,
        total_orders=len(orders),
        dine_in_sales=dine_in_sales,
        takeaway_sales=takeaway_sales,
        delivery_sales=delivery_sales,
        total_tax_collected=total_tax,
        total_discount_given=total_discount
    )

    # Tender Breakdown
    tender_rows = (
        db.query(
            RestaurantTender.method,
            func.coalesce(func.sum(RestaurantTender.amount), 0).label("amount"),
            func.count(RestaurantTender.id).label("count")
        )
        .join(RestaurantOrder, RestaurantTender.order_id == RestaurantOrder.id)
        .filter(RestaurantOrder.outlet_id == outlet_id)
        .filter(RestaurantTender.created_at >= start_dt)
        .filter(RestaurantTender.created_at <= end_dt)
        .filter(RestaurantTender.status == "COMPLETED")
        .group_by(RestaurantTender.method)
        .all()
    )

    tenders = [
        TenderSummaryItem(
            method=row.method,
            amount=Decimal(str(row.amount)),
            count=row.count
        )
        for row in tender_rows
    ]

    return DailySalesReportResponse(
        report_date=target_date,
        outlet_id=outlet_id,
        summary=summary,
        tenders=tenders
    )


from schemas.restaurant_reports import ItemSalesSummary, AuditSummaryItem
from models.restaurant_order_line import RestaurantOrderLine
from models.restaurant_audit import RestaurantAuditEvent

@router.get("/items", response_model=list[ItemSalesSummary])
def get_item_sales_report(
    outlet_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    manager_user: User = Depends(get_restaurant_manager)
):
    """
    Top selling menu items and variants with quantities and revenue generated.
    """
    s_date = start_date or date.today()
    e_date = end_date or date.today()
    start_dt = datetime.combine(s_date, datetime.min.time())
    end_dt = datetime.combine(e_date, datetime.max.time())

    item_rows = (
        db.query(
            RestaurantOrderLine.item_name,
            RestaurantOrderLine.variant_name,
            func.sum(RestaurantOrderLine.quantity).label("quantity_sold"),
            func.sum(RestaurantOrderLine.line_total).label("total_revenue")
        )
        .join(RestaurantOrder, RestaurantOrderLine.order_id == RestaurantOrder.id)
        .filter(RestaurantOrder.outlet_id == outlet_id)
        .filter(RestaurantOrder.created_at >= start_dt)
        .filter(RestaurantOrder.created_at <= end_dt)
        .filter(RestaurantOrder.status.in_(["OPEN", "SENT_TO_KITCHEN", "COMPLETED"]))
        .group_by(RestaurantOrderLine.item_name, RestaurantOrderLine.variant_name)
        .order_by(func.sum(RestaurantOrderLine.quantity).desc())
        .limit(limit)
        .all()
    )

    return [
        ItemSalesSummary(
            item_name=r.item_name,
            variant_name=r.variant_name,
            quantity_sold=r.quantity_sold,
            total_revenue=Decimal(str(r.total_revenue))
        )
        for r in item_rows
    ]


@router.get("/audits", response_model=list[AuditSummaryItem])
def get_audit_event_summary(
    outlet_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    manager_user: User = Depends(get_restaurant_manager)
):
    """
    Summary of voids, discount overrides, KOT reprints, and refunds.
    """
    s_date = start_date or date.today()
    e_date = end_date or date.today()
    start_dt = datetime.combine(s_date, datetime.min.time())
    end_dt = datetime.combine(e_date, datetime.max.time())

    audit_rows = (
        db.query(
            RestaurantAuditEvent.action,
            func.count(RestaurantAuditEvent.id).label("count")
        )
        .filter(RestaurantAuditEvent.outlet_id == outlet_id)
        .filter(RestaurantAuditEvent.created_at >= start_dt)
        .filter(RestaurantAuditEvent.created_at <= end_dt)
        .group_by(RestaurantAuditEvent.action)
        .all()
    )

    return [
        AuditSummaryItem(
            action=r.action,
            count=r.count
        )
        for r in audit_rows
    ]

