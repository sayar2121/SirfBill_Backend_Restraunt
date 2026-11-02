import os
import razorpay
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from models.database import get_db
from dependencies import get_current_user
from models.user import User
from models.inventory import InventoryItem
from models.shop_bill import ShopBill, ShopBillItem 
from models.shop import Shop

# Razorpay client
razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")

client = None
if razorpay_key_id and razorpay_key_secret:
    client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))

router = APIRouter(
    prefix="/api/orders",
    tags=["Pharmacy Orders"]
)

class OnlineCartItem(BaseModel):
    inventory_item_id: UUID
    quantity: int
    is_loose: bool = False

class OnlineCheckoutRequest(BaseModel):
    shop_id: UUID
    items: List[OnlineCartItem]
    delivery_address: Dict[str, Any]
    prescription_id: Optional[UUID] = None

@router.post("/checkout", status_code=status.HTTP_201_CREATED)
def checkout_online_order(
    request: OnlineCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient Action: Places an online pharmacy order. 
    Calculates total, locks inventory, generates a bill, and creates a Razorpay order.
    """
    total_amount = 0.0
    bill_items_to_create = []
    
    # 1. Validate stock and calculate totals
    for cart_item in request.items:
        db_inventory = db.query(InventoryItem).filter(
            InventoryItem.id == cart_item.inventory_item_id,
            InventoryItem.shop_id == request.shop_id
        ).with_for_update().first() # Lock the row to prevent race conditions
        
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
            
        total_amount += line_price
        
        bill_items_to_create.append({
            "inventory_item_id": db_inventory.id,
            "quantity": cart_item.quantity,
            "is_loose": cart_item.is_loose,
            "unit_price_at_sale": unit_price
        })

    # 2. Generate the Bill
    new_bill = ShopBill(
        tenant_id=None,
        shop_id=request.shop_id,
        user_id=current_user.id,
        # prescription_id=request.prescription_id,
        total_amount=total_amount,
        payment_method="ONLINE",
        status="PENDING_PAYMENT",
        delivery_address=request.delivery_address
    )
    
    # Inherit tenant_id from shop
    shop = db.query(Shop).filter(Shop.id == request.shop_id).first()
    if shop:
        new_bill.tenant_id = shop.tenant_id

    db.add(new_bill)
    db.flush() 
    
    # 3. Insert Line Items
    for item_data in bill_items_to_create:
        new_bill_item = ShopBillItem(
            bill_id=new_bill.id,
            **item_data
        )
        db.add(new_bill_item)
        
    db.commit()
    db.refresh(new_bill)
    
    # 4. Generate Razorpay Order
    razorpay_order_id = None
    if client and total_amount > 0:
        amount_in_paise = int(total_amount * 100)
        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": str(new_bill.id),
            "payment_capture": 1
        }
        try:
            razorpay_order = client.order.create(data=order_data)
            razorpay_order_id = razorpay_order.get("id")
        except Exception as e:
            # Optionally log failure. The order is created, patient can retry payment.
            pass

    return {
        "status": "success", 
        "message": "Order placed successfully", 
        "bill_id": new_bill.id, 
        "total": total_amount,
        "razorpay_order_id": razorpay_order_id
    }

@router.get("/history")
def get_order_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient Action: Fetch all past pharmacy orders for the logged-in user.
    """
    bills = db.query(ShopBill).filter(ShopBill.user_id == current_user.id).order_by(ShopBill.created_at.desc()).all()
    
    result = []
    for bill in bills:
        items = []
        for item in bill.items:
            inv_item = db.query(InventoryItem).filter(InventoryItem.id == item.inventory_item_id).first()
            items.append({
                "item_id": str(item.inventory_item_id),
                "name": inv_item.name if inv_item else "Unknown",
                "quantity": item.quantity,
                "unit_price_at_sale": item.unit_price_at_sale
            })
            
        result.append({
            "bill_id": str(bill.id),
            "shop_id": str(bill.shop_id),
            "total_amount": bill.total_amount,
            "payment_method": bill.payment_method,
            "status": bill.status,
            "date": bill.created_at.isoformat(),
            "items": items,
            "delivery_address": bill.delivery_address
        })
        
    return result
