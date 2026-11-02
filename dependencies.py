import os
import jwt
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import User

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-manju-key-32bytes-secret-token")
ALGORITHM = "HS256"

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """
    Validates the JWT token and returns the current user.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Returns the User if a valid Bearer token is passed; otherwise returns None (or fallback active staff).
    """
    if credentials:
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    return user
        except Exception:
            pass

    # Fallback to first active admin/staff user in database for dev/kiosk POS terminals
    fallback = db.query(User).filter(User.role.in_(["ADMIN", "OWNER", "CASHIER", "MANAGER"])).first()
    return fallback

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Validates that the current user has the ADMIN role.
    """
    if current_user.role not in ["ADMIN", "OWNER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to perform this action. Admin or Owner role required."
        )
    return current_user

def get_optional_admin_user(current_user: Optional[User] = Depends(get_optional_current_user)) -> Optional[User]:
    """
    Allows admin read operations on startup/dashboard with fallback.
    """
    return current_user

# --- Restaurant Role Dependencies ---
RESTAURANT_ROLES = ["ADMIN", "OWNER", "MANAGER", "CASHIER", "WAITER", "KITCHEN"]

def require_restaurant_roles(allowed_roles: list[str]):
    """
    Dependency factory to enforce restaurant-specific role access.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role not in ["ADMIN", "OWNER"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required role in: {allowed_roles}"
            )
        return current_user
    return role_checker

def get_restaurant_staff(current_user: User = Depends(get_current_user)) -> User:
    """Allows any restaurant staff member (WAITER, CASHIER, KITCHEN, MANAGER, OWNER, ADMIN)."""
    return require_restaurant_roles(RESTAURANT_ROLES)(current_user)

def get_optional_restaurant_staff(
    user: Optional[User] = Depends(get_optional_current_user)
) -> Optional[User]:
    """
    Permits POS read requests even before token login or in kiosk mode,
    falling back to standard staff context.
    """
    return user

def get_restaurant_manager(current_user: User = Depends(get_current_user)) -> User:
    """Allows MANAGER, OWNER, or ADMIN for audits, menu changes, discount overrides."""
    return require_restaurant_roles(["MANAGER", "OWNER", "ADMIN"])(current_user)

def get_restaurant_cashier(current_user: User = Depends(get_current_user)) -> User:
    """Allows CASHIER, MANAGER, OWNER, or ADMIN for billing and shift closure."""
    return require_restaurant_roles(["CASHIER", "MANAGER", "OWNER", "ADMIN"])(current_user)

def get_restaurant_kitchen(current_user: User = Depends(get_current_user)) -> User:
    """Allows KITCHEN staff, MANAGER, OWNER, or ADMIN for KOT status updates."""
    return require_restaurant_roles(["KITCHEN", "MANAGER", "OWNER", "ADMIN"])(current_user)

