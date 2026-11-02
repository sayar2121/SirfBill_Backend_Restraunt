from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from models.transaction import Transaction
from models.account import Account
from models.enums import TransactionType
from schemas.transaction import TransactionCreate, TransactionUpdate

def get_transaction(db: Session, transaction_id: UUID) -> Optional[Transaction]:
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def get_transactions(db: Session, shop_id: Optional[UUID] = None, tenant_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[Transaction]:
    from sqlalchemy import or_
    query = db.query(Transaction)
    if shop_id and tenant_id:
        query = query.filter(or_(Transaction.shop_id == shop_id, Transaction.tenant_id == tenant_id))
    elif shop_id:
        query = query.filter(Transaction.shop_id == shop_id)
    elif tenant_id:
        query = query.filter(Transaction.tenant_id == tenant_id)
    return query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).offset(skip).limit(limit).all()

def create_transaction(db: Session, transaction: TransactionCreate, context_tenant_id: Optional[UUID] = None) -> Transaction:
    transaction_data = transaction.model_dump()
    if context_tenant_id:
        transaction_data["tenant_id"] = context_tenant_id
        
    db_transaction = Transaction(**transaction_data)
    db.add(db_transaction)
    

    # Auto-assign to default Cash account if no accounts provided
    if not db_transaction.from_account_id and not db_transaction.to_account_id:
        cash_acc = db.query(Account).filter(
            Account.tenant_id == db_transaction.tenant_id,
            Account.name.ilike('%cash%')
        ).first()
        if not cash_acc:
            # Create a default cash account if it doesn't exist
            from models.enums import AccountType
            cash_acc = Account(
                name="Cash Account",
                account_type=AccountType.ASSET,
                balance=0.0,
                tenant_id=db_transaction.tenant_id,
                shop_id=db_transaction.shop_id
            )
            db.add(cash_acc)
            db.commit()
            db.refresh(cash_acc)
            
        if db_transaction.transaction_type == TransactionType.INCOME:
            db_transaction.to_account_id = cash_acc.id
        elif db_transaction.transaction_type == TransactionType.EXPENSE:
            db_transaction.from_account_id = cash_acc.id

    # Adjust accounts based on transaction_type if frontend only sends one account

    if db_transaction.transaction_type == TransactionType.INCOME:
        # For Income, money goes INTO the account (to_account_id)
        if db_transaction.from_account_id and not db_transaction.to_account_id:
            db_transaction.to_account_id = db_transaction.from_account_id
            db_transaction.from_account_id = None
    elif db_transaction.transaction_type == TransactionType.EXPENSE:
        # For Expense, money goes OUT OF the account (from_account_id)
        if db_transaction.to_account_id and not db_transaction.from_account_id:
            db_transaction.from_account_id = db_transaction.to_account_id
            db_transaction.to_account_id = None

    # Update account balances
    if db_transaction.from_account_id:
        from_acc = db.query(Account).filter(Account.id == db_transaction.from_account_id).first()
        if from_acc:
            if from_acc.balance < db_transaction.amount:
                raise HTTPException(
                    status_code=400,
                    detail=f"There is not enough money in {from_acc.name}. Available balance is ₹{from_acc.balance:,.2f}, but ₹{db_transaction.amount:,.2f} is required."
                )
            from_acc.balance -= db_transaction.amount
            
    if db_transaction.to_account_id:
        to_acc = db.query(Account).filter(Account.id == db_transaction.to_account_id).first()
        if to_acc:
            to_acc.balance += db_transaction.amount
            
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def update_transaction(db: Session, db_transaction: Transaction, transaction_update: TransactionUpdate) -> Transaction:
    # Reversing previous balance impact
    if db_transaction.from_account_id:
        from_acc = db.query(Account).filter(Account.id == db_transaction.from_account_id).first()
        if from_acc:
            from_acc.balance += db_transaction.amount
            
    if db_transaction.to_account_id:
        to_acc = db.query(Account).filter(Account.id == db_transaction.to_account_id).first()
        if to_acc:
            to_acc.balance -= db_transaction.amount
            
    update_data = transaction_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
        

    # Auto-assign to default Cash account if no accounts provided
    if not db_transaction.from_account_id and not db_transaction.to_account_id:
        cash_acc = db.query(Account).filter(
            Account.tenant_id == db_transaction.tenant_id,
            Account.name.ilike('%cash%')
        ).first()
        if not cash_acc:
            # Create a default cash account if it doesn't exist
            from models.enums import AccountType
            cash_acc = Account(
                name="Cash Account",
                account_type=AccountType.ASSET,
                balance=0.0,
                tenant_id=db_transaction.tenant_id,
                shop_id=db_transaction.shop_id
            )
            db.add(cash_acc)
            db.commit()
            db.refresh(cash_acc)
            
        if db_transaction.transaction_type == TransactionType.INCOME:
            db_transaction.to_account_id = cash_acc.id
        elif db_transaction.transaction_type == TransactionType.EXPENSE:
            db_transaction.from_account_id = cash_acc.id

    # Adjust accounts based on transaction_type if frontend only sends one account

    if db_transaction.transaction_type == TransactionType.INCOME:
        if db_transaction.from_account_id and not db_transaction.to_account_id:
            db_transaction.to_account_id = db_transaction.from_account_id
            db_transaction.from_account_id = None
    elif db_transaction.transaction_type == TransactionType.EXPENSE:
        if db_transaction.to_account_id and not db_transaction.from_account_id:
            db_transaction.from_account_id = db_transaction.to_account_id
            db_transaction.to_account_id = None

    # Applying new balance impact
    if db_transaction.from_account_id:
        from_acc = db.query(Account).filter(Account.id == db_transaction.from_account_id).first()
        if from_acc:
            if from_acc.balance < db_transaction.amount:
                # Re-deduct reversed amount before error so state is consistent
                from_acc.balance -= db_transaction.amount
                raise HTTPException(
                    status_code=400,
                    detail=f"There is not enough money in {from_acc.name}. Available balance is ₹{from_acc.balance + db_transaction.amount:,.2f}, but ₹{db_transaction.amount:,.2f} is required."
                )
            from_acc.balance -= db_transaction.amount
            
    if db_transaction.to_account_id:
        to_acc = db.query(Account).filter(Account.id == db_transaction.to_account_id).first()
        if to_acc:
            to_acc.balance += db_transaction.amount
            
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, db_transaction: Transaction) -> Transaction:
    # Reversing previous balance impact
    if db_transaction.from_account_id:
        from_acc = db.query(Account).filter(Account.id == db_transaction.from_account_id).first()
        if from_acc:
            from_acc.balance += db_transaction.amount
            
    if db_transaction.to_account_id:
        to_acc = db.query(Account).filter(Account.id == db_transaction.to_account_id).first()
        if to_acc:
            to_acc.balance -= db_transaction.amount
            
    db.delete(db_transaction)
    db.commit()
    return db_transaction
