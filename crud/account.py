from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional

from models.account import Account
from schemas.account import AccountCreate, AccountUpdate, AccountSummary

def get_account(db: Session, account_id: UUID) -> Optional[Account]:
    return db.query(Account).filter(Account.id == account_id).first()

def get_accounts(db: Session, shop_id: Optional[UUID] = None, tenant_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[Account]:
    query = db.query(Account)
    if shop_id:
        query = query.filter(Account.shop_id == shop_id)
    if tenant_id:
        query = query.filter(Account.tenant_id == tenant_id)
    return query.offset(skip).limit(limit).all()

def create_account(db: Session, account: AccountCreate, context_tenant_id: Optional[UUID] = None) -> Account:
    account_data = account.model_dump()
    if context_tenant_id:
        account_data["tenant_id"] = context_tenant_id
    db_account = Account(**account_data)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def update_account(db: Session, db_account: Account, account_update: AccountUpdate) -> Account:
    update_data = account_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_account, key, value)
    db.commit()
    db.refresh(db_account)
    return db_account

def delete_account(db: Session, db_account: Account) -> Account:
    db.delete(db_account)
    db.commit()
    return db_account

def get_dashboard_summary(db: Session, shop_id: Optional[UUID] = None, tenant_id: Optional[UUID] = None) -> AccountSummary:
    from models.enums import AccountType, TransactionType
    from models.transaction import Transaction
    from sqlalchemy import or_

    accounts_query = db.query(Account)
    transactions_query = db.query(func.sum(Transaction.amount))
    
    if shop_id and tenant_id:
        accounts_query = accounts_query.filter(or_(Account.shop_id == shop_id, Account.tenant_id == tenant_id))
        transactions_query = transactions_query.filter(or_(Transaction.shop_id == shop_id, Transaction.tenant_id == tenant_id))
    elif shop_id:
        accounts_query = accounts_query.filter(Account.shop_id == shop_id)
        transactions_query = transactions_query.filter(Transaction.shop_id == shop_id)
    elif tenant_id:
        accounts_query = accounts_query.filter(Account.tenant_id == tenant_id)
        transactions_query = transactions_query.filter(Transaction.tenant_id == tenant_id)
        
    accounts = accounts_query.all()
    
    cash_in_hand = sum([a.balance for a in accounts if a.account_type == AccountType.ASSET and a.name.lower() == 'cash account'])
    bank_balance = sum([a.balance for a in accounts if a.account_type == AccountType.ASSET and a.name.lower() != 'cash account'])
    
    total_income = transactions_query.filter(Transaction.transaction_type == TransactionType.INCOME).scalar() or 0.0
    total_expenses = transactions_query.filter(Transaction.transaction_type == TransactionType.EXPENSE).scalar() or 0.0
    
    net_profit = total_income - total_expenses
    
    return AccountSummary(
        cash_in_hand=cash_in_hand,
        bank_balance=bank_balance,
        total_income=total_income,
        total_expenses=total_expenses,
        net_profit=net_profit
    )
