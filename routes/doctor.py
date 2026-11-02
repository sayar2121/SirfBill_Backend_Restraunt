from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import os
import aiofiles

from schemas.doctor import DoctorCreate, DoctorUpdate, Doctor as DoctorSchema
from crud import doctor as crud_doctor
from models.database import get_db

from dependencies import get_admin_user
from models.user import User

# Note: In a real app, you would add a dependency here to check for Admin Role
router = APIRouter(
    prefix="/api/admin/doctors",
    tags=["Admin - Doctors"]
)

@router.post("/", response_model=DoctorSchema, status_code=status.HTTP_201_CREATED)
def create_doctor(
    doctor: DoctorCreate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin only: Create a new doctor profile.
    """
    return crud_doctor.create_doctor(db=db, doctor=doctor, context_tenant_id=admin_user.tenant_id)

@router.get("/", response_model=list[DoctorSchema])
def get_doctors(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    return crud_doctor.get_doctors(db, skip=skip, limit=limit)

@router.get("/{doctor_id}", response_model=DoctorSchema)
def get_doctor(
    doctor_id: UUID, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    db_doctor = crud_doctor.get_doctor(db, doctor_id=doctor_id)
    if not db_doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return db_doctor

@router.post("/{doctor_id}/upload-image", response_model=DoctorSchema)
async def upload_doctor_image(
    doctor_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin only: Upload a profile picture for a doctor.
    """
    db_doctor = crud_doctor.get_doctor(db, doctor_id=doctor_id)
    if not db_doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        raise HTTPException(status_code=400, detail="Invalid image format.")

    upload_dir = "./uploads/doctors"
    os.makedirs(upload_dir, exist_ok=True)

    file_extension = file.filename.split(".")[-1]
    file_path = f"{upload_dir}/doc_{doctor_id}.{file_extension}"
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    import time
    public_url = f"/uploads/doctors/doc_{doctor_id}.{file_extension}?v={int(time.time())}"
    
    # Update the doctor record with the new image URL
    doctor_update = DoctorUpdate(image_url=public_url)
    return crud_doctor.update_doctor(db=db, db_doctor=db_doctor, doctor_update=doctor_update)

@router.patch("/{doctor_id}", response_model=DoctorSchema)
def update_doctor(
    doctor_id: UUID, 
    doctor_update: DoctorUpdate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin only: Update an existing doctor's profile.
    """
    db_doctor = crud_doctor.get_doctor(db, doctor_id=doctor_id)
    if not db_doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Doctor not found"
        )
    
    return crud_doctor.update_doctor(db=db, db_doctor=db_doctor, doctor_update=doctor_update)

@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(
    doctor_id: UUID, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin only: Remove a doctor from the platform.
    """
    db_doctor = crud_doctor.get_doctor(db, doctor_id=doctor_id)
    if not db_doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Doctor not found"
        )
    
    crud_doctor.delete_doctor(db=db, db_doctor=db_doctor)
    return None
