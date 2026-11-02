from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from models.database import get_db
from dependencies import get_admin_user
from models.user import User
from models.purchase import PurchaseBill, PurchaseBillItem
from models.inventory import InventoryItem
from models.distributor import Distributor
from schemas.purchase import PurchaseBillCreate, PurchaseBillOut, PayPurchaseBillRequest
from models.account import Account
from models.transaction import Transaction
from models.transaction_category import TransactionCategory
from models.enums import AccountType, TransactionType

router = APIRouter(
    prefix="/api/admin/purchases",
    tags=["Admin - Purchases"]
)

@router.post("", response_model=PurchaseBillOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=PurchaseBillOut, status_code=status.HTTP_201_CREATED)
def create_purchase_bill(
    request: PurchaseBillCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Creates a purchase bill, increments inventory stock, and creates an expense transaction.
    """
    # 1. Create Purchase Bill

    new_bill = PurchaseBill(
        tenant_id=admin_user.tenant_id,
        shop_id=request.shop_id,
        distributor_id=request.distributor_id,
        invoice_no=request.invoice_no,
        bill_date=request.bill_date,
        total_amount=request.total_amount,
        subtotal=request.subtotal,
        total_discount=request.total_discount,
        total_gst=request.total_gst,
        amount_paid=request.amount_paid,
        payment_status=request.payment_status,
        payment_method=request.payment_method
    )

    db.add(new_bill)
    db.flush()
    
    # 2. Add items and update inventory
    for item in request.items:
        item_data = item.model_dump(exclude={"selling_price", "hsn_code", "rack_id", "category_id"})
        bill_item = PurchaseBillItem(
            bill_id=new_bill.id,
            **item_data
        )
        db.add(bill_item)
        
        # Handle inventory update
        if item.inventory_item_id:
            inventory = db.query(InventoryItem).filter(InventoryItem.id == item.inventory_item_id).with_for_update().first()
            if inventory:
                total_pieces_to_add = (item.quantity * inventory.pack_size) + (item.free_quantity * inventory.pack_size)
                # total_pieces_to_add = item.quantity + item.free_quantity
                
                # If a new batch is provided and differs from the existing one, create a NEW inventory item!
                if item.batch_number and item.batch_number.strip() != "" and item.batch_number.strip() != inventory.batch_number:
                    # Actually we don't need to recreate for now, just increment to avoid breaking things right now, or just let it update.
                    pass
                else:
                    pass
                
                # Same batch, just increment stock
                current_total_pieces = (inventory.stock_quantity * inventory.pack_size) + inventory.loose_stock
                new_total_pieces = current_total_pieces + total_pieces_to_add
                inventory.stock_quantity = new_total_pieces // inventory.pack_size
                inventory.loose_stock = new_total_pieces % inventory.pack_size
                
                # Increment stock
                # inventory.stock_quantity += total_pieces_to_add
                inventory.buying_price = item.unit_price
                if item.selling_price:
                    inventory.unit_price = item.selling_price
                if item.expiry_date:
                    inventory.expiry_date = item.expiry_date
                if item.hsn_code:
                    inventory.hsn_code = item.hsn_code
                if item.rack_id:
                    inventory.rack_id = item.rack_id
                if item.category_id:
                    inventory.category_id = item.category_id
                if item.gst:
                    inventory.gst = item.gst
    
    # 3. Integrate with Accounts (if payment is made)
    if request.payment_status in ["PAID", "PARTIAL"]:
        amount_to_pay = (
            request.amount_paid 
            if (request.amount_paid is not None and request.amount_paid > 0) 
            else (request.total_amount if request.payment_status == "PAID" else 0.0)
        )
        
        if amount_to_pay > 0:
            account = None
            if request.payment_method:
                account_name = "Cash Account" if request.payment_method.upper() == "CASH" else "Bank Account"
                account = db.query(Account).filter(
                    Account.name.ilike(f"%{account_name}%"),
                    Account.tenant_id == admin_user.tenant_id,
                    Account.shop_id == request.shop_id
                ).first()

            if not account:
                account = db.query(Account).filter(
                    Account.shop_id == request.shop_id,
                    Account.account_type == AccountType.ASSET,
                    Account.balance >= amount_to_pay
                ).first()

            if not account:
                account = db.query(Account).filter(
                    Account.shop_id == request.shop_id,
                    Account.account_type == AccountType.ASSET
                ).first()

            if not account:
                account = db.query(Account).filter(
                    Account.tenant_id == admin_user.tenant_id,
                    Account.account_type == AccountType.ASSET
                ).first()

            if not account:
                raise HTTPException(
                    status_code=400,
                    detail="There is no money in the accounts section. No active payment account found. Please add an account with money first."
                )

            if account.balance < amount_to_pay:
                raise HTTPException(
                    status_code=400,
                    detail=f"There is not enough money in the accounts section ({account.name}). Available balance: ₹{account.balance:,.2f}, required: ₹{amount_to_pay:,.2f}."
                )

            account.balance -= amount_to_pay
            new_bill.amount_paid = amount_to_pay

            category = db.query(TransactionCategory).filter(
                TransactionCategory.name == "Inventory Purchase",
                TransactionCategory.tenant_id == admin_user.tenant_id
            ).first()
            if not category:
                category = TransactionCategory(
                    name="Inventory Purchase",
                    transaction_type=TransactionType.EXPENSE,
                    tenant_id=admin_user.tenant_id
                )
                db.add(category)
                db.flush()

            distributor = db.query(Distributor).filter(Distributor.id == request.distributor_id).first()
            distributor_name = distributor.name if distributor else "Unknown Distributor"

            transaction = Transaction(
                reference_number=f"PUR-{str(new_bill.id)[:8].upper()}",
                description=f"Purchase from Distributor - {request.invoice_no or 'Auto'}",
                amount=amount_to_pay,
                transaction_type=TransactionType.EXPENSE,
                tenant_id=request.shop_id or admin_user.tenant_id,
                shop_id=request.shop_id,
                category_id=category.id,
                from_account_id=account.id,
                entity_name=distributor_name,
                entity_type="SUPPLIER",
                status="PAID"
            )
            db.add(transaction)

    db.commit()
    db.refresh(new_bill)
    return new_bill

@router.get("", response_model=List[PurchaseBillOut], include_in_schema=False)
@router.get("/", response_model=List[PurchaseBillOut])
def get_purchase_bills(
    shop_id: Optional[UUID] = None,
    distributor_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    query = db.query(PurchaseBill)
    if shop_id:
        query = query.filter(PurchaseBill.shop_id == shop_id)
    if distributor_id:
        query = query.filter(PurchaseBill.distributor_id == distributor_id)
    if admin_user.tenant_id:
        query = query.filter(PurchaseBill.tenant_id == admin_user.tenant_id)
        
    return query.order_by(PurchaseBill.created_at.desc()).all()


@router.patch("/{bill_id}/pay")
def pay_purchase_bill(
    bill_id: UUID,
    payload: Optional[PayPurchaseBillRequest] = None,
    account_id: Optional[UUID] = Query(None),
    payment_method: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    bill = db.query(PurchaseBill).filter(PurchaseBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    if bill.payment_status == "PAID":
        raise HTTPException(status_code=400, detail="Bill is already paid")

    # Calculate remaining amount to pay
    amount_to_pay = bill.total_amount - (bill.amount_paid or 0.0)
    if amount_to_pay <= 0:
        amount_to_pay = bill.total_amount

    # Resolve account and payment method
    selected_account_id = (payload.account_id if payload else None) or account_id
    selected_method = (payload.payment_method if payload else None) or payment_method or bill.payment_method or "CASH"

    account = None
    if selected_account_id:
        account = db.query(Account).filter(Account.id == selected_account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Selected payment account not found.")

    if not account and selected_method:
        if selected_method.upper() == "CASH":
            account = db.query(Account).filter(
                Account.shop_id == bill.shop_id,
                Account.name.ilike("%cash%"),
                Account.account_type == AccountType.ASSET
            ).first()
        else:
            account = db.query(Account).filter(
                Account.shop_id == bill.shop_id,
                ~Account.name.ilike("%cash%"),
                Account.account_type == AccountType.ASSET
            ).first()

    # If no account matched method, look for an asset account with enough balance
    if not account:
        account = db.query(Account).filter(
            Account.shop_id == bill.shop_id,
            Account.account_type == AccountType.ASSET,
            Account.balance >= amount_to_pay
        ).first()

    # Fallback to any asset account for the shop
    if not account:
        account = db.query(Account).filter(
            Account.shop_id == bill.shop_id,
            Account.account_type == AccountType.ASSET
        ).first()

    # Fallback to tenant asset account
    if not account:
        account = db.query(Account).filter(
            Account.tenant_id == (bill.tenant_id or admin_user.tenant_id),
            Account.account_type == AccountType.ASSET
        ).first()

    # Validate that account exists
    if not account:
        raise HTTPException(
            status_code=400,
            detail="There is no money in the accounts section. No active payment account found. Please create an account with funds first."
        )

    # Validate sufficient funds in the accounts section
    if account.balance < amount_to_pay:
        raise HTTPException(
            status_code=400,
            detail=f"There is not enough money in the accounts section ({account.name}). Available balance: ₹{account.balance:,.2f}, required: ₹{amount_to_pay:,.2f}."
        )

    # Deduct balance
    account.balance -= amount_to_pay
    bill.payment_status = "PAID"
    bill.amount_paid = bill.total_amount
    bill.payment_method = selected_method

    # Resolve category
    category = db.query(TransactionCategory).filter(
        TransactionCategory.name == "Inventory Purchase",
        TransactionCategory.tenant_id == admin_user.tenant_id
    ).first()
    if not category:
        category = TransactionCategory(
            name="Inventory Purchase",
            transaction_type=TransactionType.EXPENSE,
            tenant_id=admin_user.tenant_id
        )
        db.add(category)
        db.flush()

    distributor = db.query(Distributor).filter(Distributor.id == bill.distributor_id).first()
    distributor_name = distributor.name if distributor else "Unknown Distributor"

    # Record expense transaction
    expense_txn = Transaction(
        tenant_id=bill.shop_id or bill.tenant_id or admin_user.tenant_id,
        shop_id=bill.shop_id,
        from_account_id=account.id,
        amount=amount_to_pay,
        transaction_type=TransactionType.EXPENSE,
        category_id=category.id,
        entity_name=distributor_name,
        entity_type="SUPPLIER",
        status="PAID",
        description=f"Purchase Bill Invoice: {bill.invoice_no or 'Auto'}",
        reference_number=f"PB-{str(bill.id)[:8].upper()}"
    )
    db.add(expense_txn)

    db.commit()
    db.refresh(bill)
    return {
        "status": "success",
        "message": f"Bill marked as paid using {account.name}. Remaining balance: ₹{account.balance:,.2f}",
        "account_name": account.name,
        "remaining_balance": account.balance
    }


from fastapi.responses import StreamingResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors

@router.get("/{bill_id}/pdf")
def generate_purchase_bill_pdf(
    bill_id: UUID,
    db: Session = Depends(get_db)
):
    bill = db.query(PurchaseBill).filter(PurchaseBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    distributor = db.query(Distributor).filter(Distributor.id == bill.distributor_id).first()
    dist_name = distributor.name if distributor else "Unknown"
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "PURCHASE BILL (INVOICE)")
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Invoice No: {bill.invoice_no or 'Auto'}")
    c.drawString(50, height - 85, f"Date: {bill.bill_date}")
    c.drawString(50, height - 100, f"Distributor: {dist_name}")
    
    # Items Table Header
    c.drawString(50, height - 130, "Item")
    c.drawString(200, height - 130, "Qty")
    c.drawString(240, height - 130, "Price")
    c.drawString(290, height - 130, "Disc%")
    c.drawString(330, height - 130, "GST%")
    c.drawString(370, height - 130, "Total")
    
    c.line(50, height - 135, width - 50, height - 135)
    
    y = height - 150
    for item in bill.items:
        # fetch item name
        inv_item = db.query(InventoryItem).filter(InventoryItem.id == item.inventory_item_id).first()
        name = inv_item.name if inv_item else "Unknown"
        
        c.drawString(50, y, name[:25])
        c.drawString(200, y, str(item.quantity))
        c.drawString(240, y, f"{item.unit_price:.2f}")
        c.drawString(290, y, f"{item.discount:.1f}%")
        c.drawString(330, y, f"{item.gst:.1f}%")
        total = (item.quantity * item.unit_price)
        total = total - (total * (item.discount/100))
        total = total + (total * (item.gst/100))
        c.drawString(370, y, f"{total:.2f}")
        y -= 20
        
    c.line(50, y, width - 50, y)
    y -= 20
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(250, y, "Subtotal:")
    c.drawString(350, y, f"{bill.subtotal:.2f}")
    y -= 15
    c.drawString(250, y, "Total Discount:")
    c.drawString(350, y, f"-{bill.total_discount:.2f}")
    y -= 15
    c.drawString(250, y, "Total GST:")
    c.drawString(350, y, f"+{bill.total_gst:.2f}")
    y -= 15
    c.drawString(250, y, "Grand Total:")
    c.drawString(350, y, f"Rs {bill.total_amount:.2f}")
    y -= 15
    c.drawString(250, y, "Amount Paid:")
    c.drawString(350, y, f"Rs {bill.amount_paid:.2f}")
    
    y -= 30
    c.drawString(50, y, f"Status: {bill.payment_status}")
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=Purchase_{bill.id}.pdf"})
