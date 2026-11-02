from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class PaymentCreateRequest(BaseModel):
    tenant_id: Optional[UUID] = None
    user_id: UUID
    amount: float
    module_type: str
    module_id: UUID

class PaymentVerificationRequest(BaseModel):
    payment_record_id: UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentResponse(BaseModel):
    id: UUID
    tenant_id: Optional[UUID] = None
    user_id: UUID
    amount: float
    status: str
    module_type: str
    module_id: UUID
    razorpay_order_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
