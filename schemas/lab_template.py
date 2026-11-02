from pydantic import BaseModel
from typing import List, Optional, Any

class TemplateFieldSchema(BaseModel):
    name: str
    shortCode: Optional[str] = ""
    unit: str
    normalRange: str
    resultType: Optional[str] = "Numeric"
    decimals: Optional[int] = 1

class DoctorSignatureSchema(BaseModel):
    doctorName: str
    qualifications: str
    designation: str
    signatureImageUrl: Optional[str] = ""

class ReportLayoutConfigSchema(BaseModel):
    clinicName: Optional[str] = "Manju Medical Stores & Digital Clinic"
    clinicAddress: Optional[str] = "123, Main Road, Kolkata - 700001"
    clinicPhone: Optional[str] = "+91 98765 43210"
    clinicEmail: Optional[str] = "lab@manjumedical.com"
    headerLogoUrl: Optional[str] = ""
    signatures: Optional[List[DoctorSignatureSchema]] = []
    qrCodeUrl: Optional[str] = ""
    playStoreUrl: Optional[str] = ""
    footerBannerUrl: Optional[str] = ""
    footerColorHex: Optional[str] = "#EA580C"

class LabTemplateBase(BaseModel):
    id: str
    name: str
    testName: Optional[str] = ""
    category: Optional[str] = "General"
    type: Optional[str] = "Standard"
    reportFormat: Optional[str] = "PDF"
    isActive: Optional[bool] = True
    description: Optional[str] = ""
    showPatientDetails: Optional[bool] = True
    showReferrals: Optional[bool] = True
    showLabLogo: Optional[bool] = True
    showRemarksSection: Optional[bool] = True
    defaultRemarks: Optional[str] = ""
    fields: Optional[List[Any]] = []
    layoutConfig: Optional[Any] = {}

class LabTemplateCreate(LabTemplateBase):
    pass

class LabTemplateUpdate(BaseModel):
    name: Optional[str]
    testName: Optional[str]
    category: Optional[str]
    type: Optional[str]
    reportFormat: Optional[str]
    isActive: Optional[bool]
    description: Optional[str]
    showPatientDetails: Optional[bool]
    showReferrals: Optional[bool]
    showLabLogo: Optional[bool]
    showRemarksSection: Optional[bool]
    defaultRemarks: Optional[str]
    fields: Optional[List[Any]]
    layoutConfig: Optional[Any]
