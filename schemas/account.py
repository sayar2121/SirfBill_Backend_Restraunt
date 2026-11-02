from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from models.enums import AccountType

class AccountBase(BaseModel):
    name: str
    account_type: AccountType
    tenant_id: Optional[UUID] = None

class AccountCreate(AccountBase):
    balance: Optional[float] = 0.0

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[AccountType] = None
    balance: Optional[float] = None

class AccountResponse(AccountBase):
    id: UUID
    balance: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AccountSummary(BaseModel):
    cash_in_hand: float
    bank_balance: float
    total_income: float
    total_expenses: float
    net_profit: float
