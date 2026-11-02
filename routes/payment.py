import os
import razorpay
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from models.database import get_db
from schemas.payment import PaymentCreateRequest, PaymentVerificationRequest, PaymentResponse
from crud import payment as crud_payment

router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"]
)

# Create a sync function for the background work
def process_post_payment_actions(db: Session, payment_record: PaymentResponse):
    pass

# Initialize Razorpay Client
razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")

client = None
if razorpay_key_id and razorpay_key_secret:
    client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))

@router.post("/create-order", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_order(request: PaymentCreateRequest, db: Session = Depends(get_db)):
    """
    Creates an order in Razorpay and stores a pending transaction in our database.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Razorpay credentials not configured.")

    # Razorpay expects amount in paise (multiply INR by 100)
    amount_in_paise = int(request.amount * 100)
    
    order_data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "payment_capture": 1 # Auto capture
    }
    
    try:
        # Create Order on Razorpay
        razorpay_order = client.order.create(data=order_data)
        
        # Save pending payment to DB
        payment_record = crud_payment.create_payment_record(
            db=db, 
            request=request, 
            razorpay_order_id=razorpay_order["id"]
        )
        
        return payment_record
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify", response_model=PaymentResponse)
def verify_payment(
    request: PaymentVerificationRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Verifies the signature sent by frontend from Razorpay.
    If valid, updates the Payment record to SUCCESS, and updates the associated module.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Razorpay credentials not configured.")
        
    payment_record = crud_payment.get_payment_record(db, payment_id=request.payment_record_id)
    if not payment_record:
        raise HTTPException(status_code=404, detail="Payment record not found.")
        
    if payment_record.status == "SUCCESS":
        return payment_record # Already processed
        
    # Verify Signature
    params_dict = {
        'razorpay_order_id': request.razorpay_order_id,
        'razorpay_payment_id': request.razorpay_payment_id,
        'razorpay_signature': request.razorpay_signature
    }
    
    try:
        # This will raise a SignatureVerificationError if invalid
        client.utility.verify_payment_signature(params_dict)
        
        # 1. Update Payment Status to SUCCESS
        payment_record = crud_payment.update_payment_success(
            db=db, 
            payment=payment_record,
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_signature=request.razorpay_signature
        )
        
        # 2. Hand off the heavy lifting to the background task
        background_tasks.add_task(process_post_payment_actions, db, payment_record)
        
        return payment_record
        
    except razorpay.errors.SignatureVerificationError:
        # Invalid signature, mark failed
        crud_payment.update_payment_failed(db, payment_record)
        raise HTTPException(status_code=400, detail="Invalid payment signature. Verification failed.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
