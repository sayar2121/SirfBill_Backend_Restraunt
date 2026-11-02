import sys
content = open('crud/transaction.py').read()

new_logic = """
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
"""

content = content.replace("    # Adjust accounts based on transaction_type if frontend only sends one account", new_logic)
open('crud/transaction.py', 'w').write(content)
print("Updated crud/transaction.py")
