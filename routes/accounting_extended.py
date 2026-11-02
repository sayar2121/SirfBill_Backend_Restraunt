from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime

from models.database import get_db
from models.transaction import Transaction
from models.account import Account
from models.purchase import PurchaseBill
from models.distributor import Distributor
from models.enums import TransactionType, AccountType

router = APIRouter(
    prefix="/api/accounts/extended",
    tags=["Extended Accounting"]
)

@router.get("/receivables")
def get_receivables(db: Session = Depends(get_db)):
    # Receivables: transactions where entity_type == 'CUSTOMER' and status == 'UNPAID' or 'PARTIAL'
    # Actually, simpler: just return all customers and their outstanding balance based on transactions.
    # Group by entity_name.
    
    results = (
        db.query(
            Transaction.entity_name,
            func.sum(Transaction.amount).label("total_owed")
        )
        .filter(Transaction.entity_type == 'CUSTOMER')
        .filter(Transaction.status.in_(['UNPAID', 'PARTIAL']))
        .group_by(Transaction.entity_name)
        .all()
    )
    
    data = []
    total_receivables = 0.0
    for row in results:
        data.append({
            "entity_name": row.entity_name,
            "amount_owed": row.total_owed
        })
        total_receivables += row.total_owed
        
    return {
        "status": "success",
        "data": {
            "receivables": data,
            "total_receivables": total_receivables
        }
    }

@router.get("/payables")
def get_payables(shop_id: Optional[str] = None, db: Session = Depends(get_db)):
    data = []
    total_payables = 0.0

    # 1. Outstanding Purchase Bills
    bills_query = db.query(PurchaseBill).filter(
        PurchaseBill.payment_status.in_(['UNPAID', 'PARTIAL', 'PENDING'])
    )
    if shop_id:
        try:
            from uuid import UUID
            bills_query = bills_query.filter(PurchaseBill.shop_id == UUID(shop_id))
        except Exception:
            pass
    bills = bills_query.order_by(PurchaseBill.created_at.desc()).all()

    for bill in bills:
        amount_owed = (bill.total_amount or 0.0) - (bill.amount_paid or 0.0)
        if amount_owed > 0:
            dist = db.query(Distributor).filter(Distributor.id == bill.distributor_id).first() if bill.distributor_id else None
            supplier_name = dist.name if dist else (f"Invoice #{bill.invoice_no}" if bill.invoice_no else "Supplier")
            
            data.append({
                "id": str(bill.id),
                "bill_id": str(bill.id),
                "entity_name": supplier_name,
                "invoice_no": bill.invoice_no or "N/A",
                "amount_owed": round(amount_owed, 2),
                "total_amount": round(bill.total_amount, 2),
                "amount_paid": round(bill.amount_paid or 0.0, 2),
                "payment_status": bill.payment_status,
                "bill_date": str(bill.bill_date) if bill.bill_date else "",
                "type": "PURCHASE_BILL"
            })
            total_payables += amount_owed

    # 2. General Supplier Transactions (UNPAID/PARTIAL)
    txn_query = (
        db.query(
            Transaction.entity_name,
            func.sum(Transaction.amount).label("total_owed")
        )
        .filter(Transaction.entity_type == 'SUPPLIER')
        .filter(Transaction.status.in_(['UNPAID', 'PARTIAL']))
    )
    if shop_id:
        try:
            from uuid import UUID
            txn_query = txn_query.filter(Transaction.shop_id == UUID(shop_id))
        except Exception:
            pass
    txn_results = txn_query.group_by(Transaction.entity_name).all()

    for row in txn_results:
        if not any(d.get("entity_name") == row.entity_name for d in data):
            data.append({
                "id": None,
                "bill_id": None,
                "entity_name": row.entity_name or "Unknown Supplier",
                "invoice_no": "-",
                "amount_owed": round(row.total_owed, 2),
                "total_amount": round(row.total_owed, 2),
                "amount_paid": 0.0,
                "payment_status": "UNPAID",
                "bill_date": "",
                "type": "TRANSACTION"
            })
            total_payables += row.total_owed

    return {
        "status": "success",
        "data": {
            "payables": data,
            "total_payables": round(total_payables, 2)
        }
    }

@router.get("/ledger")
def get_ledger(db: Session = Depends(get_db)):
    # Returns all accounts and their current balances
    accounts = db.query(Account).all()
    data = []
    for acc in accounts:
        data.append({
            "id": str(acc.id),
            "name": acc.name,
            "type": acc.account_type.value,
            "balance": acc.balance
        })
        
    return {
        "status": "success",
        "data": data
    }

@router.get("/reports/pnl")
def get_pnl(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Transaction)
    if start_date:
        query = query.filter(Transaction.date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Transaction.date <= datetime.fromisoformat(end_date))
        
    income = query.filter(Transaction.transaction_type == TransactionType.INCOME).with_entities(func.sum(Transaction.amount)).scalar() or 0.0
    expense = query.filter(Transaction.transaction_type == TransactionType.EXPENSE).with_entities(func.sum(Transaction.amount)).scalar() or 0.0
    
    return {
        "status": "success",
        "data": {
            "total_income": income,
            "total_expense": expense,
            "net_profit": income - expense
        }
    }
