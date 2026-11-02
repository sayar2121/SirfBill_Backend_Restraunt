from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from models.database import get_db
from dependencies import get_admin_user, get_optional_admin_user
from models.user import User
from models import InventoryItem, ShopBill, ShopBillItem 
# from models.print_job import PrintJob
from models.account import Account
from models.transaction import Transaction
from models.transaction_category import TransactionCategory
from models.enums import AccountType, TransactionType 

router = APIRouter(
    prefix="/api/admin/pos",
    tags=["Admin - Point of Sale"]
)

from typing import Optional

class POSCartItem(BaseModel):
    inventory_item_id: Optional[UUID] = None
    print_job_id: Optional[UUID] = None
    item_name: Optional[str] = None
    unit_price: Optional[float] = 0.0
    quantity: int = 1
    is_loose: bool = False
    discount: float = 0.0
    gst: float = 0.0

class POSCheckoutRequest(BaseModel):
    shop_id: UUID
    user_id: UUID = None # Optional, if linking to a specific patient CRM profile[cite: 1]
    prescription_id: UUID = None
    invoice_no: str = None
    customer_name: str = None
    customer_phone: str = None
    customer_location: str = None
    customer_gstin: str = None
    items: List[POSCartItem]
    payment_method: str = "CASH"
    
    # Financials
    subtotal: float = 0.0
    total_discount: float = 0.0
    total_gst: float = 0.0
    total_amount: float = None # final amount
    amount_paid: float = 0.0
    payment_status: str = "PAID" # UNPAID, PARTIAL, PAID

@router.post("/checkout", status_code=status.HTTP_201_CREATED)
def process_sale(
    request: POSCheckoutRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED: Pharmacist/Admin
):
    """
    Admin Action: Processes a pharmacy sale and instantly deducts inventory[cite: 1].
    """
    calculated_total = 0.0
    bill_items_to_create = []
    
    # 1. Validate stock and calculate totals
    for cart_item in request.items:
        if cart_item.inventory_item_id:
            db_inventory = db.query(InventoryItem).filter(
                InventoryItem.id == cart_item.inventory_item_id,
                InventoryItem.shop_id == request.shop_id
            ).with_for_update().first() # Lock the row to prevent race conditions during deduction
            
            if not db_inventory:
                raise HTTPException(status_code=404, detail=f"Item {cart_item.inventory_item_id} not found.")
                
            total_pieces_available = (db_inventory.stock_quantity * db_inventory.pack_size) + db_inventory.loose_stock
            # total_pieces_available = db_inventory.stock_quantity
            
            if cart_item.is_loose:
                pieces_to_sell = cart_item.quantity
                if total_pieces_available < pieces_to_sell:
                    raise HTTPException(status_code=400, detail=f"Insufficient loose stock for {db_inventory.name}. Only {total_pieces_available} pieces left.")
                
                total_pieces_after = total_pieces_available - pieces_to_sell
                db_inventory.stock_quantity = total_pieces_after // db_inventory.pack_size
                db_inventory.loose_stock = total_pieces_after % db_inventory.pack_size
                
                unit_price = db_inventory.unit_price / db_inventory.pack_size
                line_price = unit_price * cart_item.quantity
            else:
                pieces_to_sell = cart_item.quantity * db_inventory.pack_size
                if total_pieces_available < pieces_to_sell:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for {db_inventory.name}. Only {db_inventory.stock_quantity} packs left.")
                    
                total_pieces_after = total_pieces_available - pieces_to_sell
                db_inventory.stock_quantity = total_pieces_after // db_inventory.pack_size
                db_inventory.loose_stock = total_pieces_after % db_inventory.pack_size
                
                unit_price = db_inventory.unit_price
                line_price = unit_price * cart_item.quantity
                
            item_name = db_inventory.name
            inv_id = db_inventory.id
            pj_id = None
        elif cart_item.print_job_id:
            raise HTTPException(status_code=400, detail="Print jobs are not supported in Restaurant billing mode.")
        elif cart_item.item_name:
            # Custom / Ad-hoc Item
            unit_price = float(cart_item.unit_price or 0.0)
            line_price = unit_price * cart_item.quantity
            item_name = cart_item.item_name
            inv_id = None
            pj_id = None
        else:
            continue
            
        calculated_total += line_price
        
        # Calculate item-level financials
        item_discount = (cart_item.discount / 100) * line_price if cart_item.discount > 0 else 0
        item_after_discount = line_price - item_discount
        item_gst = (cart_item.gst / 100) * item_after_discount if cart_item.gst > 0 else 0
        item_final_price = item_after_discount + item_gst
        
        bill_items_to_create.append({
            "inventory_item_id": inv_id,
            "print_job_id": pj_id,
            "item_name": item_name,
            "quantity": cart_item.quantity,
            "is_loose": cart_item.is_loose,
            "unit_price_at_sale": unit_price,
            "discount_at_sale": cart_item.discount,
            "gst_at_sale": cart_item.gst,
            "total_price": item_final_price
        })

    # Use the frontend-provided total if present (to account for GST, discounts), else fallback to strict calculation
    final_amount = request.total_amount if request.total_amount is not None else calculated_total

    # 2. Generate the Bill[cite: 1]
    new_bill = ShopBill(
        tenant_id=admin_user.tenant_id,
        shop_id=request.shop_id,
        user_id=request.user_id,
        # prescription_id=request.prescription_id,
        invoice_no=request.invoice_no,
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        customer_location=request.customer_location,
        customer_gstin=request.customer_gstin,
        subtotal=request.subtotal or calculated_total,
        total_discount=request.total_discount,
        total_gst=request.total_gst,
        total_amount=final_amount,
        amount_paid=request.amount_paid,
        payment_method=request.payment_method,
        payment_status=request.payment_status
    )
    db.add(new_bill)
    db.flush() # Get the new_bill.id without committing yet
    
    # 3. Insert Line Items
    for item_data in bill_items_to_create:
        new_bill_item = ShopBillItem(
            bill_id=new_bill.id,
            **item_data
        )
        db.add(new_bill_item)
        
    # 4. Integrate with Accounts Module
    account_name = "Cash Account" if request.payment_method == "CASH" else "Bank Account"
    
    # Find or create account
    account = db.query(Account).filter(Account.name == account_name, Account.shop_id == request.shop_id).first()
    if not account:
        account = Account(name=account_name, account_type=AccountType.ASSET, tenant_id=request.shop_id, shop_id=request.shop_id)
        db.add(account)
        db.flush()
        
    # Find or create POS Sales category
    category = db.query(TransactionCategory).filter(TransactionCategory.name == "POS Sales", TransactionCategory.tenant_id == request.shop_id).first()
    if not category:
        category = TransactionCategory(name="POS Sales", transaction_type=TransactionType.INCOME, tenant_id=request.shop_id)
        db.add(category)
        db.flush()
        
    # Record the Income Transaction
    transaction = Transaction(
        reference_number=f"POS-{str(new_bill.id)[:8].upper()}",
        description=f"POS Sale - {request.payment_method}",
        amount=final_amount,
        transaction_type=TransactionType.INCOME,
        tenant_id=request.shop_id,
        shop_id=request.shop_id,
        category_id=category.id,
        to_account_id=account.id
    )
    db.add(transaction)
    
    # Update account balance
    account.balance += final_amount

    db.commit()
    db.refresh(new_bill)
    
    return {"message": "Sale completed successfully", "bill_id": new_bill.id, "total": final_amount}

from models.shop import Shop
from models.restaurant_outlet import RestaurantOutlet

@router.get("/history")
def get_pos_history(
    shop_id: UUID,
    tenant_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: Optional[User] = Depends(get_optional_admin_user)
):
    """
    Admin Action: Fetches the history of all bills for a specific shop, along with summary stats.
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == shop_id).first()
        if outlet:
            # Fallback or alias to shop if outlet ID is passed
            shop = db.query(Shop).filter(Shop.id == outlet.shop_id).first() if outlet.shop_id else None
            if not shop:
                shop = db.query(Shop).filter(Shop.tenant_id == outlet.tenant_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # If tenant_id query param matches shop's tenant or ID, or user tenant matches
    effective_tenant_id = tenant_id or (admin_user.tenant_id if admin_user else None)
    if admin_user and admin_user.tenant_id and shop.tenant_id != admin_user.tenant_id:
        # Check if tenant_id param explicitly provided and matches shop tenant or shop id
        if tenant_id and (shop.tenant_id == tenant_id or shop.id == tenant_id):
            pass
        else:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
    bills = db.query(ShopBill).filter(ShopBill.shop_id == shop_id).order_by(ShopBill.created_at.desc()).all()
    
    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year
    
    # previous month
    prev_month = current_month - 1
    prev_year = current_year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    current_month_bills = [b for b in bills if b.created_at.month == current_month and b.created_at.year == current_year]
    prev_month_bills = [b for b in bills if b.created_at.month == prev_month and b.created_at.year == prev_year]

    cm_bills = len(current_month_bills)
    pm_bills = len(prev_month_bills)
    
    cm_sales = sum(b.total_amount for b in current_month_bills)
    pm_sales = sum(b.total_amount for b in prev_month_bills)
    
    cm_customers = len(set(b.user_id for b in current_month_bills if b.user_id))
    pm_customers = len(set(b.user_id for b in prev_month_bills if b.user_id))

    cm_items = sum(sum(i.quantity for i in b.items) for b in current_month_bills)
    pm_items = sum(sum(i.quantity for i in b.items) for b in prev_month_bills)

    def calc_growth(current, previous):
        if previous == 0:
            return "+100%" if current > 0 else "0%"
        growth = ((current - previous) / previous) * 100
        sign = "+" if growth >= 0 else ""
        return f"{sign}{growth:.1f}%"

    growth_bills = calc_growth(cm_bills, pm_bills)
    growth_sales = calc_growth(cm_sales, pm_sales)
    growth_customers = calc_growth(cm_customers, pm_customers)
    growth_items = calc_growth(cm_items, pm_items)

    total_bills = len(bills)
    total_sales = sum(bill.total_amount for bill in bills)
    customers_served = len(set(bill.user_id for bill in bills if bill.user_id))
    
    total_items = 0
    history_list = []
    
    for bill in bills:
        # Sum quantities for this bill
        items_count = sum(item.quantity for item in bill.items)
        total_items += items_count
        
        items_detail = []
        for item in bill.items:
            inventory_item = db.query(InventoryItem).filter(InventoryItem.id == item.inventory_item_id).first() if item.inventory_item_id else None
            item_name = inventory_item.name if inventory_item else (item.item_name or "Custom Item")
            hsn_code = str(inventory_item.hsn_code) if inventory_item and inventory_item.hsn_code else "-"
            gst_val = float(inventory_item.gst or 0.0) if inventory_item else float(getattr(item, 'gst_at_sale', 0.0) or 0.0)
            expiry = inventory_item.expiry_date.strftime("%Y-%m-%d") if inventory_item and inventory_item.expiry_date else "-"
            unit_price = float(item.unit_price_at_sale or 0.0)
            items_detail.append({
                "name": item_name,
                "qty": item.quantity,
                "price": unit_price,
                "mrp": unit_price,
                "expiry": expiry,
                "hsn": hsn_code,
                "cgst": round(gst_val / 2, 2),
                "sgst": round(gst_val / 2, 2),
                "total": round(unit_price * item.quantity, 2)
            })
            
        customer_name = bill.customer_name or "Walk-in Customer"
        if bill.user_id:
            user = db.query(User).filter(User.id == bill.user_id).first()
            if user:
                customer_name = user.name
                
        # Generate a short friendly ref number from the UUID if not provided
        ref_no = bill.invoice_no if bill.invoice_no else str(bill.id).split('-')[0].upper()
                
        history_list.append({
            "id": str(bill.id),
            "date": bill.created_at.isoformat(),
            "bill_no": ref_no,
            "customer_name": customer_name,
            "customer_phone": bill.customer_phone or "",
            "customer_location": bill.customer_location or "",
            "customer_gstin": bill.customer_gstin or "",
            "type": "POS Sale" if not bill.delivery_address else "Online Order",
            "items": items_count,
            "items_detail": items_detail,
            "amount": bill.total_amount,
            "payment_mode": bill.payment_method,
            "status": bill.status or "COMPLETED"
        })
        
    # Apply pagination for the history list
    paginated_list = history_list[skip : skip + limit]
    
    return {
        "summary": {
            "total_bills": total_bills,
            "total_sales": total_sales,
            "customers_served": customers_served,
            "items_sold": total_items,
            "growth_bills": growth_bills,
            "growth_sales": growth_sales,
            "growth_customers": growth_customers,
            "growth_items": growth_items
        },
        "history": paginated_list
    }

from fastapi.responses import StreamingResponse
from utils.pdf_generator import generate_shop_bill_pdf
from models.shop import Shop

@router.get("/bills/{bill_id}/pdf")
def get_bill_pdf(
    bill_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Generate and return PDF for a POS Bill.
    """
    bill = db.query(ShopBill).filter(ShopBill.id == bill_id, ShopBill.tenant_id == admin_user.tenant_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    shop = db.query(Shop).filter(Shop.id == bill.shop_id).first()
    
    pdf_buffer = generate_shop_bill_pdf(bill, shop)
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"inline; filename=pos_bill_{bill_id}.pdf"}
    )
