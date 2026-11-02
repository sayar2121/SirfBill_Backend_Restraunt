from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from crud import transaction as crud_transaction
from models.database import get_db

router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"]
)

@router.get("", response_model=List[TransactionResponse])
def get_transactions(
    shop_id: Optional[UUID] = None,
    tenant_id: Optional[UUID] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    List all transactions
    """
    return crud_transaction.get_transactions(db, shop_id=shop_id, tenant_id=tenant_id, skip=skip, limit=limit)

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    """
    Create a new transaction
    """
    return crud_transaction.create_transaction(db=db, transaction=transaction)

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: UUID, db: Session = Depends(get_db)):
    db_transaction = crud_transaction.get_transaction(db, transaction_id=transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction

@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: UUID, transaction_update: TransactionUpdate, db: Session = Depends(get_db)):
    db_transaction = crud_transaction.get_transaction(db, transaction_id=transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return crud_transaction.update_transaction(db=db, db_transaction=db_transaction, transaction_update=transaction_update)

@router.delete("/{transaction_id}", response_model=TransactionResponse)
def delete_transaction(transaction_id: UUID, db: Session = Depends(get_db)):
    db_transaction = crud_transaction.get_transaction(db, transaction_id=transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return crud_transaction.delete_transaction(db=db, db_transaction=db_transaction)
