from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from schemas.account import AccountCreate, AccountUpdate, AccountResponse, AccountSummary
from crud import account as crud_account
from models.database import get_db

router = APIRouter(
    prefix="/api/accounts",
    tags=["Accounts"]
)

from typing import List, Optional

@router.get("/summary", response_model=AccountSummary)
def get_dashboard_summary(shop_id: Optional[UUID] = None, tenant_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    """
    Get dashboard summary metrics (Cash, Bank, Income, Expenses, Net Profit)
    """
    return crud_account.get_dashboard_summary(db, shop_id=shop_id, tenant_id=tenant_id)

@router.get("", response_model=List[AccountResponse])
def get_accounts(shop_id: Optional[UUID] = None, tenant_id: Optional[UUID] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all accounts
    """
    return crud_account.get_accounts(db, shop_id=shop_id, tenant_id=tenant_id, skip=skip, limit=limit)

@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """
    Create a new account
    """
    return crud_account.create_account(db=db, account=account)

@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: UUID, db: Session = Depends(get_db)):
    db_account = crud_account.get_account(db, account_id=account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account

@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(account_id: UUID, account_update: AccountUpdate, db: Session = Depends(get_db)):
    db_account = crud_account.get_account(db, account_id=account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    return crud_account.update_account(db=db, db_account=db_account, account_update=account_update)

@router.delete("/{account_id}", response_model=AccountResponse)
def delete_account(account_id: UUID, db: Session = Depends(get_db)):
    db_account = crud_account.get_account(db, account_id=account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    return crud_account.delete_account(db=db, db_account=db_account)
