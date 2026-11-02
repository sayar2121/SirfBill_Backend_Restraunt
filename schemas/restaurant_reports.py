from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
from pydantic import BaseModel

class SalesSummaryReport(BaseModel):
    total_sales: Decimal
    total_orders: int
    dine_in_sales: Decimal
    takeaway_sales: Decimal
    delivery_sales: Decimal
    total_tax_collected: Decimal
    total_discount_given: Decimal

class TenderSummaryItem(BaseModel):
    method: str
    amount: Decimal
    count: int

class DailySalesReportResponse(BaseModel):
    report_date: date
    outlet_id: UUID
    summary: SalesSummaryReport
    tenders: List[TenderSummaryItem]

class ItemSalesSummary(BaseModel):
    item_name: str
    variant_name: str
    quantity_sold: int
    total_revenue: Decimal

class AuditSummaryItem(BaseModel):
    action: str
    count: int

