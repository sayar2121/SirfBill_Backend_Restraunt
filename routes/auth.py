import random
import httpx
import os
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from models.database import get_db
from models.user import User
from models.otp import OTPStore
from schemas.auth import SendOTPRequest, VerifyOTPRequest, AdminLoginRequest

from dependencies import SECRET_KEY, ALGORITHM, get_current_user

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

@router.post("/send-otp")
async def send_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """
    Step 1: Generates a random OTP, saves it to the DB, and sends it via APITXT.
    """
    # 1. Generate a random 4-digit OTP
    generated_otp = str(random.randint(1000, 9999))
    
    # 2. Save/Update the OTP in our database with a 5-minute expiration
    expiration_time = datetime.utcnow() + timedelta(minutes=5)
    
    existing_otp = db.query(OTPStore).filter(OTPStore.phone == request.phone).first()
    if existing_otp:
        existing_otp.otp_code = generated_otp
        existing_otp.expires_at = expiration_time
    else:
        new_otp = OTPStore(phone=request.phone, otp_code=generated_otp, expires_at=expiration_time)
        db.add(new_otp)
    
    db.commit()

    # ==========================================
    # 🧪 TESTING MODE: BYPASS APITXT
    # ==========================================
    TEST_NUMBERS = ["919999999999", "918888888888"]
    
    if request.phone in TEST_NUMBERS:
        db_otp = db.query(OTPStore).filter(OTPStore.phone == request.phone).first()
        db_otp.otp_code = "1234"
        db.commit()
        
        print(f"🛠️ APP STORE TEST MODE: Bypassed APITXT for {request.phone}. Use OTP: 1234")
        return {"message": "Test OTP mapped successfully"}
        
    # 3. Send the OTP using APITXT API (Production)
    apitxt_url = "https://apitxt.com/api/sendOTP"
    apitxt_auth_key = os.getenv("APITXT_AUTH_KEY", "YOUR_AUTH_KEY_HERE")
    
    payload = {
        "authkey": apitxt_auth_key,
        "mobile": request.phone,
        "otp": generated_otp,
        "channel": request.channel,
        "country": "91"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(apitxt_url, data=payload)
            response_data = response.json()
            
            if response_data.get("status") == "success":
                return {"message": f"OTP sent successfully via {request.channel}"}
            else:
                print("APITXT Error:", response_data)
                raise HTTPException(status_code=500, detail="Failed to send OTP via provider")
                
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to SMS provider: {str(e)}")

@router.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Step 2: Checks if the OTP matches. If valid, logs the user in (or creates their account).
    """
    # 1. Find the OTP record in the database
    db_otp = db.query(OTPStore).filter(OTPStore.phone == request.phone).first()
    
    if not db_otp:
        raise HTTPException(status_code=400, detail="No OTP requested for this number")
        
    # 2. Check if OTP is expired
    if datetime.utcnow() > db_otp.expires_at:
        db.delete(db_otp)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
        
    # 3. Check if OTP matches
    if db_otp.otp_code != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    # 4. Success! OTP is valid. Clean it up so it can't be reused.
    db.delete(db_otp)
    
    # 5. Check if this is an existing user or a new registration
    user = db.query(User).filter(User.phone == request.phone).first()
    
    if not user:
        # Create a new user if they don't exist
        user = User(
            phone=request.phone,
            name=request.name,
            role="USER"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        is_new_user = True
    else:
        is_new_user = False

    # Generate JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "message": "Login successful",
        "access_token": access_token,
        "user_id": str(user.id),
        "is_new_user": is_new_user,
        "role": user.role
    }

from models.restaurant_outlet import RestaurantOutlet

@router.post("/admin-login")
@router.post("/admin/login")
def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    """
    Admin / Staff Login using Email and Password.
    Returns access token, user role, and assigned restaurant outlet info.
    """
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if user.role not in ["ADMIN", "OWNER", "MANAGER", "CASHIER", "KITCHEN", "WAITER"]:
        raise HTTPException(status_code=403, detail="You do not have access privileges")
        
    # Plain text password comparison (no hashing)
    if user.password != request.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    # Generate JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Fetch assigned outlet or default to tenant/active outlet
    outlet = None
    if user.outlet_id:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == user.outlet_id).first()
    if not outlet:
        outlet_query = db.query(RestaurantOutlet).filter(RestaurantOutlet.is_active == True)
        if user.tenant_id:
            outlet_query = outlet_query.filter(RestaurantOutlet.tenant_id == user.tenant_id)
        outlet = outlet_query.first() or db.query(RestaurantOutlet).first()

    return {
        "message": "Admin Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "role": user.role,
        "name": user.name,
        "email": user.email,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "outlet_id": str(user.outlet_id) if user.outlet_id else (str(outlet.id) if outlet else None),
        "assigned_outlet_id": str(user.outlet_id) if user.outlet_id else None,
        "outlet": {
            "id": str(outlet.id) if outlet else None,
            "name": outlet.name if outlet else "SirfBill Grand Restaurant",
            "code": outlet.code if outlet else "SB-01"
        } if outlet else None
    }
