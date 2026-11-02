import sys
sys.path.append('.')
from models.database import SessionLocal
from models.user import User

session = SessionLocal()
users = session.query(User).all()
for u in users:
    print(f"Email: {u.email}, Role: {u.role}, Password: {u.password}")
