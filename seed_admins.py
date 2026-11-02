from models.database import SessionLocal
from models.user import User

db = SessionLocal()

admins_to_create = [
    {"email": "admin_counter", "password": "password", "role": "ADMIN", "name": "Counter Admin", "phone": "counter_phone"},
    {"email": "admin_crm", "password": "password", "role": "ADMIN", "name": "CRM Admin", "phone": "crm_phone"},
    {"email": "admin_lab", "password": "password", "role": "ADMIN", "name": "Lab Admin", "phone": "lab_phone"},
]

for admin_data in admins_to_create:
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == admin_data["email"]).first()
    if existing_user:
        print(f"User {admin_data['email']} already exists. Updating password.")
        existing_user.password = admin_data["password"]
    else:
        new_admin = User(**admin_data)
        db.add(new_admin)
        print(f"Created user {admin_data['email']}.")

db.commit()
db.close()
print("Done.")
