from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from models.lab_template import LabTemplate
from schemas.lab_template import LabTemplateCreate, LabTemplateUpdate, LabTemplateBase

router = APIRouter(prefix="/api/admin/lab-template", tags=["Admin - Lab Templates"])

def _to_camel(obj: LabTemplate):
    return {
        "id": obj.id,
        "name": obj.name,
        "testName": obj.test_name,
        "category": obj.category,
        "type": obj.type,
        "reportFormat": obj.report_format,
        "isActive": obj.is_active,
        "description": obj.description,
        "showPatientDetails": obj.show_patient_details,
        "showReferrals": obj.show_referrals,
        "showLabLogo": obj.show_lab_logo,
        "showRemarksSection": obj.show_remarks_section,
        "defaultRemarks": obj.default_remarks,
        "fields": obj.fields,
        "layoutConfig": obj.layout_config,
    }

@router.get("/")
def get_templates(db: Session = Depends(get_db)):
    templates = db.query(LabTemplate).all()
    return [_to_camel(t) for t in templates]

@router.get("/{template_id}")
def get_template(template_id: str, db: Session = Depends(get_db)):
    template = db.query(LabTemplate).filter(LabTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _to_camel(template)

@router.post("/")
def create_template(data: LabTemplateCreate, db: Session = Depends(get_db)):
    db_template = LabTemplate(
        id=data.id,
        name=data.name,
        test_name=data.testName,
        category=data.category,
        type=data.type,
        report_format=data.reportFormat,
        is_active=data.isActive,
        description=data.description,
        show_patient_details=data.showPatientDetails,
        show_referrals=data.showReferrals,
        show_lab_logo=data.showLabLogo,
        show_remarks_section=data.showRemarksSection,
        default_remarks=data.defaultRemarks,
        fields=data.fields,
        layout_config=data.layoutConfig
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return _to_camel(db_template)

@router.patch("/{template_id}")
def update_template(template_id: str, data: LabTemplateUpdate, db: Session = Depends(get_db)):
    db_template = db.query(LabTemplate).filter(LabTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = data.dict(exclude_unset=True)
    mapping = {
        "testName": "test_name",
        "reportFormat": "report_format",
        "isActive": "is_active",
        "showPatientDetails": "show_patient_details",
        "showReferrals": "show_referrals",
        "showLabLogo": "show_lab_logo",
        "showRemarksSection": "show_remarks_section",
        "defaultRemarks": "default_remarks",
        "layoutConfig": "layout_config",
    }
    
    for k, v in update_data.items():
        db_key = mapping.get(k, k)
        setattr(db_template, db_key, v)
        
    db.commit()
    db.refresh(db_template)
    return _to_camel(db_template)

@router.delete("/{template_id}")
def delete_template(template_id: str, db: Session = Depends(get_db)):
    db_template = db.query(LabTemplate).filter(LabTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(db_template)
    db.commit()
    return {"status": "deleted"}
