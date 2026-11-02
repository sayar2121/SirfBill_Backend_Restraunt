from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from models.payment import Payment
from schemas.payment import PaymentCreateRequest

def create_payment_record(db: Session, request: PaymentCreateRequest, razorpay_order_id: str, context_tenant_id: Optional[UUID] = None) -> Payment:
    tenant_id_to_use = context_tenant_id if context_tenant_id else request.tenant_id
    db_payment = Payment(
        tenant_id=tenant_id_to_use,
        user_id=request.user_id,
        amount=request.amount,
        module_type=request.module_type,
        module_id=request.module_id,
        razorpay_order_id=razorpay_order_id,
        status="PENDING"
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payment_record(db: Session, payment_id: UUID) -> Optional[Payment]:
    return db.query(Payment).filter(Payment.id == payment_id).first()

def update_payment_success(
    db: Session, 
    payment: Payment, 
    razorpay_payment_id: str, 
    razorpay_signature: str
) -> Payment:
    payment.status = "SUCCESS"
    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    db.commit()
    db.refresh(payment)
    return payment

def update_payment_failed(db: Session, payment: Payment) -> Payment:
    payment.status = "FAILED"
    db.commit()
    db.refresh(payment)
    return payment
