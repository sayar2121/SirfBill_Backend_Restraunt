from models.database import SessionLocal
from models.inventory import InventoryItem

db = SessionLocal()

try:
    # Get all items where manufacturer is not null
    items = db.query(InventoryItem).filter(InventoryItem.manufacturer.isnot(None)).all()
    count = 0
    for item in items:
        # Copy manufacturer to distributor
        item.distributor = item.manufacturer
        count += 1
            
    db.commit()
    print(f"Successfully copied manufacturer to distributor for {count} items!")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
