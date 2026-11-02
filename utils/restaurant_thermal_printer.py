import os
from decimal import Decimal
import datetime
try:
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")
except Exception:
    IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def format_local_time(dt) -> str:
    if not dt:
        dt = datetime.datetime.now(IST)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc).astimezone(IST)
    else:
        dt = dt.astimezone(IST)
    return dt.strftime("%d/%m/%Y %I:%M %p")

from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

# 80mm standard thermal roll width
RECEIPT_WIDTH = 76 * mm
MARGIN = 3 * mm
CONTENT_WIDTH = RECEIPT_WIDTH - (2 * MARGIN)

def ensure_upload_dirs():
    os.makedirs("uploads/kots", exist_ok=True)
    os.makedirs("uploads/bills", exist_ok=True)
    os.makedirs("uploads/inventory", exist_ok=True)

def generate_kot_pdf(ticket, order, table_name="Takeaway", outlet_name="SirfBill Restaurant") -> str:
    """
    Generates an 80mm thermal receipt PDF for a KOT and stores it in uploads/kots/
    Returns the relative URL path /uploads/kots/...
    """
    ensure_upload_dirs()
    filename = f"{ticket.ticket_number}_{ticket.id.hex[:6]}.pdf"
    file_path = os.path.join("uploads", "kots", filename)

    # Setup styles
    styles = getSampleStyleSheet()
    center_bold = ParagraphStyle(
        'CenterBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        alignment=1
    )
    center_sub = ParagraphStyle(
        'CenterSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=1
    )
    left_bold = ParagraphStyle(
        'LeftBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11
    )
    left_regular = ParagraphStyle(
        'LeftRegular',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )
    right_bold = ParagraphStyle(
        'RightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        alignment=2
    )

    elements = []

    # Header
    elements.append(Paragraph(outlet_name.upper(), center_bold))
    elements.append(Spacer(1, 1 * mm))
    elements.append(Paragraph(f"KITCHEN ORDER TICKET ({ticket.station})", center_bold))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=2*mm, spaceAfter=2*mm))

    # Metadata grid
    created_str = format_local_time(ticket.created_at)
    meta_data = [
        [Paragraph(f"<b>KOT #:</b> {ticket.ticket_number}", left_regular), Paragraph(f"<b>Table:</b> {table_name}", right_bold)],
        [Paragraph(f"<b>Order #:</b> {order.order_number}", left_regular), Paragraph(f"<b>Type:</b> {order.order_type}", right_bold)],
        [Paragraph(f"<b>Date:</b> {created_str}", left_regular), ""]
    ]
    t_meta = Table(meta_data, colWidths=[CONTENT_WIDTH * 0.55, CONTENT_WIDTH * 0.45])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(t_meta)
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=2*mm, spaceAfter=2*mm))

    # Items table
    items_data = [
        [Paragraph("<b>QTY</b>", left_bold), Paragraph("<b>ITEM DESCRIPTION</b>", left_bold)]
    ]

    for item in ticket.items:
        desc = f"<b>{item.item_name}</b>"
        if item.variant_name and item.variant_name != "Standard":
            desc += f" <i>({item.variant_name})</i>"
        if item.special_instructions:
            desc += f"<br/><font color='grey'>Note: {item.special_instructions}</font>"
        if item.modifiers_summary:
            desc += f"<br/><font color='grey'>+ {item.modifiers_summary}</font>"

        items_data.append([
            Paragraph(f"<b>{item.quantity}x</b>", left_bold),
            Paragraph(desc, left_regular)
        ])

    t_items = Table(items_data, colWidths=[CONTENT_WIDTH * 0.22, CONTENT_WIDTH * 0.78])
    t_items.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
    ]))
    elements.append(t_items)
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=3*mm, spaceAfter=2*mm))

    # Footer note
    elements.append(Paragraph("*** FOR KITCHEN USE ONLY ***", center_sub))

    # Dynamic height calculation to guarantee everything stays strictly on ONE continuous roll page:
    # Header: ~30mm, Meta: ~22mm, Items: ~6.5mm/item, Footer: ~10mm, buffer: ~8mm
    num_items = len(ticket.items) if ticket.items else 1
    doc_height = (70 + (num_items * 7.5)) * mm
    doc = SimpleDocTemplate(
        file_path,
        pagesize=(RECEIPT_WIDTH, doc_height),
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )
    doc.build(elements)

    return f"/uploads/kots/{filename}"


def generate_bill_pdf(order, outlet, table_name="Takeaway") -> str:
    """
    Generates an 80mm thermal receipt PDF for a customer bill and stores it in uploads/bills/
    Returns the relative URL path /uploads/bills/...
    """
    ensure_upload_dirs()
    filename = f"{order.order_number}_{order.id.hex[:6]}.pdf"
    file_path = os.path.join("uploads", "bills", filename)

    styles = getSampleStyleSheet()
    center_bold = ParagraphStyle(
        'CenterBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=15,
        alignment=1
    )
    center_sub = ParagraphStyle(
        'CenterSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=1
    )
    left_bold = ParagraphStyle(
        'LeftBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10
    )
    left_regular = ParagraphStyle(
        'LeftRegular',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )
    right_regular = ParagraphStyle(
        'RightRegular',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=2
    )
    right_bold = ParagraphStyle(
        'RightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        alignment=2
    )

    elements = []

    # Restaurant Branding Header
    # 0. Restaurant Logo (if configured)
    logo_file = None
    if outlet and outlet.logo_url:
        cleaned_path = outlet.logo_url.lstrip("/")
        if os.path.exists(cleaned_path):
            logo_file = cleaned_path
    elif outlet and outlet.service_settings and outlet.service_settings.get("logo_url"):
        cleaned_path = str(outlet.service_settings.get("logo_url")).lstrip("/")
        if os.path.exists(cleaned_path):
            logo_file = cleaned_path

    if logo_file:
        try:
            elements.append(RLImage(logo_file, width=32*mm, height=18*mm))
            elements.append(Spacer(1, 1.5*mm))
        except Exception:
            pass

    outlet_name = outlet.name if outlet else "SirfBill Restaurant"
    elements.append(Paragraph(outlet_name.upper(), center_bold))
    if outlet and outlet.address:
        elements.append(Paragraph(outlet.address, center_sub))
    if outlet and outlet.phone:
        elements.append(Paragraph(f"Tel: {outlet.phone}", center_sub))
    if outlet and outlet.gstin:
        elements.append(Paragraph(f"GSTIN: {outlet.gstin}", center_sub))
    if outlet and outlet.fssai:
        elements.append(Paragraph(f"FSSAI: {outlet.fssai}", center_sub))

    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=2*mm, spaceAfter=2*mm))
    elements.append(Paragraph("TAX INVOICE", center_bold))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1*mm, spaceAfter=2*mm))

    # Meta Info
    date_str = format_local_time(order.created_at)
    meta_data = [
        [Paragraph(f"<b>Bill No:</b> {order.order_number}", left_regular), Paragraph(f"<b>Table:</b> {table_name}", right_bold)],
        [Paragraph(f"<b>Type:</b> {order.order_type}", left_regular), Paragraph(f"<b>Date:</b> {date_str}", right_regular)],
    ]
    cust_name = order.customer_name or "Walk-in Guest"
    cust_phone = f" ({order.customer_phone})" if getattr(order, 'customer_phone', None) else ""
    meta_data.append([Paragraph(f"<b>Customer:</b> {cust_name}{cust_phone}", left_regular), ""])

    t_meta = Table(meta_data, colWidths=[CONTENT_WIDTH * 0.55, CONTENT_WIDTH * 0.45])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(t_meta)
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=2*mm, spaceAfter=2*mm))

    # Order Line Items Table
    lines_data = [
        [Paragraph("<b>ITEM</b>", left_bold), Paragraph("<b>QTY</b>", left_bold), Paragraph("<b>RATE</b>", right_bold), Paragraph("<b>TOTAL</b>", right_bold)]
    ]

    # Consolidate duplicate order lines by (item_name, variant_name, unit_price)
    consolidated_lines = {}
    for line in order.lines:
        item_title = line.item_name
        if line.variant_name and line.variant_name != "Standard":
            item_title += f" ({line.variant_name})"
        effective_rate = float(line.unit_price) + float(getattr(line, 'modifier_price', 0.0) or 0.0)
        base_line_total = effective_rate * int(line.quantity)
        key = (item_title, effective_rate)
        if key in consolidated_lines:
            consolidated_lines[key]['qty'] += int(line.quantity)
            consolidated_lines[key]['total'] += base_line_total
        else:
            consolidated_lines[key] = {
                'title': item_title,
                'qty': int(line.quantity),
                'price': effective_rate,
                'total': base_line_total
            }

    for item in consolidated_lines.values():
        lines_data.append([
            Paragraph(item['title'], left_regular),
            Paragraph(str(item['qty']), left_regular),
            Paragraph(f"{item['price']:.2f}", right_regular),
            Paragraph(f"{item['total']:.2f}", right_regular),
        ])

    t_lines = Table(lines_data, colWidths=[CONTENT_WIDTH * 0.44, CONTENT_WIDTH * 0.14, CONTENT_WIDTH * 0.20, CONTENT_WIDTH * 0.22])
    t_lines.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
    ]))
    elements.append(t_lines)
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=2*mm, spaceAfter=2*mm))

    # Financial Summary
    summary_data = [
        [Paragraph("Subtotal:", left_regular), Paragraph(f"Rs. {float(order.subtotal):.2f}", right_regular)]
    ]
    if order.discount_amount and float(order.discount_amount) > 0:
        summary_data.append([Paragraph("Discount:", left_regular), Paragraph(f"-Rs. {float(order.discount_amount):.2f}", right_regular)])
    
    # Detailed GST Breakup (Intra-state: CGST 2.5% + SGST 2.5%)
    tax_amt = float(order.tax_amount or 0.0)
    if tax_amt > 0:
        half_tax = tax_amt / 2.0
        summary_data.append([Paragraph("CGST (2.5%):", left_regular), Paragraph(f"Rs. {half_tax:.2f}", right_regular)])
        summary_data.append([Paragraph("SGST (2.5%):", left_regular), Paragraph(f"Rs. {half_tax:.2f}", right_regular)])
    
    if order.rounding_adjustment and abs(float(order.rounding_adjustment)) > 0:
        summary_data.append([Paragraph("Round Off:", left_regular), Paragraph(f"Rs. {float(order.rounding_adjustment):+.2f}", right_regular)])

    summary_data.append([Paragraph("<b>GRAND TOTAL:</b>", left_bold), Paragraph(f"<b>Rs. {float(order.grand_total):.2f}</b>", right_bold)])
    summary_data.append([Paragraph("<b>PAID AMOUNT:</b>", left_bold), Paragraph(f"<b>Rs. {float(order.paid_amount):.2f}</b>", right_bold)])

    t_sum = Table(summary_data, colWidths=[CONTENT_WIDTH * 0.55, CONTENT_WIDTH * 0.45])
    t_sum.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEABOVE', (0, -2), (-1, -2), 0.5, colors.black),
    ]))
    elements.append(t_sum)

    # Footer greetings
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=3*mm, spaceAfter=2*mm))
    elements.append(Paragraph("THANK YOU FOR DINING WITH US!", center_bold))
    elements.append(Paragraph("Please visit again", center_sub))

    # Dynamic height calculation to guarantee continuous fit on ONE roll page without large trailing gaps:
    # Header: ~32mm, Meta: ~18mm, Items: ~5.5mm/item, Summary: ~20mm, Footer: ~12mm
    num_items = len(consolidated_lines) if consolidated_lines else 1
    doc_height = max(150, (135 + (num_items * 9.0))) * mm
    doc = SimpleDocTemplate(
        file_path,
        pagesize=(RECEIPT_WIDTH, doc_height),
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )
    doc.build(elements)

    return f"/uploads/bills/{filename}"
