import uuid
import random
from models.database import SessionLocal
from models.distributor import Distributor
from sqlalchemy.orm import Session

# Shop and Tenant IDs provided by user
SHOP_ID = uuid.UUID("705dbbf7-494b-421e-b3c5-86dd2b473fdc")
TENANT_ID = uuid.UUID("4abe49c4-5269-4577-b8c6-b1f7466ff755")

raw_distributors = [
    "Dr. Reddy's", "Cipla", "Aurobindo", "Zydus Cadila", "Cipla", "Torrent Pharma",
    "Torrent Pharma", "Sun Pharma", "Mankind", "Torrent Pharma", "Alkem",
    "Mankind", "Zydus Cadila", "Aurobindo", "Aurobindo", "Mankind", "Cipla", "Intas",
    "deb", "Dr. Reddy's", "ABC", "Zydus Cadila", "Intas", "Dr. Reddy's", "Lupin",
    "Zydus Cadila", "Torrent Pharma", "Sun Pharma", "Alkem", "Torrent Pharma",
    "Torrent Pharma", "Aurobindo", "Lupin", "Zydus Cadila", "Torrent Pharma", "Intas",
    "Torrent Pharma", "Zydus Cadila", "Dr. Reddy's", "Torrent Pharma", "Cipla",
    "Torrent Pharma", "Zydus Cadila", "Lupin", "Sun Pharma", "Alkem", "Sun Pharma",
    "Sun Pharma", "Alkem", "Zydus Cadila", "Cipla", "Aurobindo", "Aurobindo",
    "Sun Pharma", "Sun Pharma", "GG", "Debu Pharma", "Intas", "Cipla", "Aurobindo",
    "Zydus Cadila", "Torrent Pharma", "Aurobindo", "Intas", "TORRENT PHARMA",
    "Torrent Pharma", "Dr. Reddy's", "Sun Pharma", "Sun Pharma", "Zydus Cadila",
    "Mankind", "Lupin", "Cipla", "Lupin", "Lupin", "Dr. Reddy's", "Torrent Pharma",
    "Torrent Pharma", "wings pharma", "Lupin", "Lupin", "Aurobindo", "Cipla",
    "Zydus Cadila", "Zydus Cadila", "Mankind", "Alkem", "Sun Pharma", "Cipla", "Intas",
    "Torrent Pharma", "Aurobindo", "Dr. Reddy's", "Lupin", "Dr. Reddy's", "Mankind",
    "Torrent Pharma", "Sun Pharma", "Lupin", "Zydus Cadila", "Dr. Reddy's", "Cipla",
    "Intas", "Aurobindo", "Alkem", "Torrent Pharma", "Aurobindo", "Intas", "Aurobindo",
    "Aurobindo"
]

# Deduplicate (case-insensitive)
unique_distributors = {}
for name in raw_distributors:
    key = name.lower()
    if key not in unique_distributors:
        # Keep the original casing for the first occurrence (except if it's all caps, maybe title case it)
        display_name = name.title() if name.isupper() else name
        unique_distributors[key] = display_name

first_names = ["Rajesh", "Amit", "Vikram", "Suresh", "Rahul", "Pooja", "Neha", "Anil", "Sunil", "Karan", "Rohit", "Deepak"]
last_names = ["Sharma", "Verma", "Patel", "Singh", "Gupta", "Kumar", "Das", "Roy", "Nair", "Reddy"]
cities = ["Mumbai, Maharashtra", "Delhi, NCR", "Bangalore, Karnataka", "Hyderabad, Telangana", "Ahmedabad, Gujarat", "Chennai, Tamil Nadu", "Kolkata, West Bengal", "Pune, Maharashtra"]
streets = ["M.G. Road", "Link Road", "Station Road", "Industrial Area", "Phase 1", "Market Road", "Business Park"]

db: Session = SessionLocal()

try:
    for _, dist_name in unique_distributors.items():
        # Check if exists
        existing = db.query(Distributor).filter(Distributor.name == dist_name, Distributor.shop_id == SHOP_ID).first()
        if existing:
            print(f"Skipping {dist_name} (already exists)")
            continue
            
        contact_person = f"{random.choice(first_names)} {random.choice(last_names)}"
        # Generate realistic phone
        phone = f"+91 {random.randint(90000, 99999)}{random.randint(10000, 99999)}"
        # Generate email
        email_prefix = contact_person.lower().replace(" ", ".")
        domain = dist_name.lower().replace(" ", "").replace("'", "").replace(".", "") + ".com"
        if len(domain) < 5:
            domain = "distributors.com"
        email = f"{email_prefix}@{domain}"
        
        # Generate Address
        address = f"Plot No. {random.randint(1, 200)}, {random.choice(streets)}, {random.choice(cities)} - {random.randint(110000, 790000)}"
        
        # Generate GSTIN (2 chars state code + 10 alphanumeric PAN + 3 alphanumeric)
        state_code = str(random.randint(10, 37))
        pan = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5)) + \
              "".join(random.choices("0123456789", k=4)) + \
              random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        suffix = f"1Z{random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
        gstin = f"{state_code}{pan}{suffix}"
        
        new_dist = Distributor(
            tenant_id=TENANT_ID,
            shop_id=SHOP_ID,
            name=dist_name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address,
            gstin=gstin,
            notes="Added via automated seeding script."
        )
        db.add(new_dist)
        print(f"Added distributor: {dist_name}")
        
    db.commit()
    print("Successfully seeded all distributors!")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
