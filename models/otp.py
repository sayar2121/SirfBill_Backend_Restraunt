from sqlalchemy import Column, String, DateTime
from models.database import Base

class OTPStore(Base):
    """Stores OTPs temporarily for verification."""
    __tablename__ = "otp_codes"
    
    phone = Column(String, primary_key=True, index=True)
    otp_code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
