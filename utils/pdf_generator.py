import io
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_lab_receipt_pdf(booking):
    """
    Generates a PDF receipt for a Lab Booking using ReportLab.
    Returns a BytesIO buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading2']
    title_style.alignment = 1 # Center
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    
    elements = []
    
    # Logo
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'manju_logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path)
        logo.drawHeight = 1.0 * inch
        logo.drawWidth = 1.0 * inch
        elements.append(logo)
        elements.append(Spacer(1, 0.1 * inch))
        
    # Header
    elements.append(Paragraph("<b>Manju Medical Stores and Digital Clinic</b>", title_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    receipt_title = styles['Heading3']
    receipt_title.alignment = 1
    elements.append(Paragraph("Lab Test Booking Receipt", receipt_title))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Booking Details
    patient_name = booking.form_details.get('patient_name', 'N/A') if booking.form_details else 'N/A'
    preferred_date = booking.preferred_date or "N/A"
    booking_id_str = "..." + str(booking.id)[-4:]
    payment_method = booking.payment_method or "N/A"
    status = booking.status
    
    # Fix layout to give more space for long UUID
    details_data = [
        [Paragraph("<b>Booking ID:</b>", bold_style), booking_id_str, Paragraph("<b>Date:</b>", bold_style), preferred_date],
        [Paragraph("<b>Patient Name:</b>", bold_style), patient_name, Paragraph("<b>Payment:</b>", bold_style), payment_method],
        [Paragraph("<b>Status:</b>", bold_style), status, "", ""]
    ]
    
    # 7 inches total width
    details_table = Table(details_data, colWidths=[1.0*inch, 2.0*inch, 0.7*inch, 1.2*inch])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 0.4 * inch))
    
    # Items Table
    table_data = [['#', 'Test Name', 'Price (Rs)']]
    
    total_amount = 0
    if isinstance(booking.booked_items, list):
        for idx, item in enumerate(booking.booked_items, start=1):
            title = item.get('title', 'Unknown Test')
            price = item.get('price', 0)
            total_amount += float(price)
            table_data.append([str(idx), title, f"Rs. {price:.2f}"])
    
    table_data.append(['', 'Total Amount', f"Rs. {total_amount:.2f}"])
    
    items_table = Table(table_data, colWidths=[0.4*inch, 3.4*inch, 1.1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C8B5F")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        # Styling for Total row
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (1, -1), (-1, -1), 1, colors.black),
        ('LINEBELOW', (1, -1), (-1, -1), 2, colors.black),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.6 * inch))
    
    # Footer
    footer_style = styles['Normal']
    footer_style.alignment = 1
    elements.append(Paragraph("Thank you for choosing Manju Medical Stores and Digital Clinic.", footer_style))
    elements.append(Paragraph("For any queries, please contact our support.", footer_style))
    
    # Build
    doc.build(elements)
    
    buffer.seek(0)
    return buffer


def generate_shop_bill_pdf(bill, shop) -> io.BytesIO:
    buffer = io.BytesIO()
    # A5 size for typical pharmacy receipts
    doc = SimpleDocTemplate(buffer, pagesize=A5, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ShopTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=5,
        alignment=1 # Center
    )
    
    # Header: Shop details
    shop_name = shop.name if shop else "Pharmacy"
    shop_address = shop.address if shop and getattr(shop, 'address', None) else ""
    elements.append(Paragraph(f"<b>{shop_name}</b>", title_style))
    if shop_address:
        elements.append(Paragraph(shop_address, ParagraphStyle('Center', alignment=1)))
    elements.append(Spacer(1, 10))
    
    # Bill Details
    bill_info = [
        [f"Invoice No: {bill.invoice_no or str(bill.id)[:8].upper()}", f"Date: {bill.created_at.strftime('%Y-%m-%d %H:%M')}"],
        [f"Customer: {bill.customer_name or 'Walk-in'}", f"Status: {bill.payment_status}"],
    ]
    if getattr(bill, 'customer_phone', None):
        bill_info.append([f"Phone: {bill.customer_phone}", f"Payment: {bill.payment_method}"])
        
    info_table = Table(bill_info, colWidths=[200, 150])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))
    
    # Items Table
    data = [["Item", "Qty", "Price", "Disc", "GST", "Total"]]
    for item in bill.items:
        # Resolve item name
        inv_item = getattr(item, "inventory_item", None)
        item_name = inv_item.name if inv_item else (item.item_name or "Custom Item")
        data.append([
            item_name[:20],
            str(item.quantity),
            f"{item.unit_price_at_sale:.2f}",
            f"{getattr(item, 'discount_at_sale', 0.0)}%",
            f"{getattr(item, 'gst_at_sale', 0.0)}%",
            f"{getattr(item, 'total_price', item.unit_price_at_sale * item.quantity):.2f}"
        ])
        
    # Totals Row
    data.append(["", "", "", "", "Subtotal:", f"{getattr(bill, 'subtotal', bill.total_amount):.2f}"])
    data.append(["", "", "", "", "Discount:", f"- {getattr(bill, 'total_discount', 0.0):.2f}"])
    data.append(["", "", "", "", "GST:", f"+ {getattr(bill, 'total_gst', 0.0):.2f}"])
    data.append(["", "", "", "", "Total:", f"{bill.total_amount:.2f}"])
    data.append(["", "", "", "", "Paid:", f"{getattr(bill, 'amount_paid', bill.total_amount):.2f}"])
    
    t = Table(data, colWidths=[120, 30, 45, 45, 45, 60])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEABOVE', (-2, -5), (-1, -5), 1, colors.black), # line above subtotal
        ('FONTNAME', (-2, -5), (-1, -1), 'Helvetica-Bold'), # bold totals
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Thank you for your visit!", ParagraphStyle('Center', alignment=1)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
