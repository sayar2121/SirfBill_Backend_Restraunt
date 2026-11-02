from models.database import SessionLocal
from models.inventory import InventoryItem
from models.distributor import Distributor

db = SessionLocal()

try:
    items = db.query(InventoryItem).filter(InventoryItem.manufacturer.isnot(None), InventoryItem.distributor_id.is_(None)).all()
    count = 0
    for item in items:
        # Case insensitive match
        dist_name = item.manufacturer.strip().lower()
        # Find distributor with this name in the same shop
        distributor = db.query(Distributor).filter(
            Distributor.shop_id == item.shop_id,
            Distributor.name.ilike(f"%{dist_name}%")
        ).first()
        
        if distributor:
            item.distributor_id = distributor.id
            count += 1
            
    db.commit()
    print(f"Successfully linked {count} inventory items to their respective distributors!")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
