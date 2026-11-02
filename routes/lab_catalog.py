from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import csv
import io

from schemas.lab_catalog import LabCatalogCreate, LabCatalogUpdate, LabCatalog as LabCatalogSchema
from crud import lab_catalog as crud_lab_catalog
from models.lab_catalog import LabCatalog as LabCatalogModel
from models.database import get_db
from dependencies import get_admin_user
from models.user import User

router = APIRouter(
    prefix="/api/admin/lab-catalog",
    tags=["Admin - Lab Catalog"]
)

@router.post("/upload-csv", status_code=status.HTTP_201_CREATED)
async def upload_lab_catalog_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin Action: Bulk upload lab tests using a CSV file.
    Expected columns: title, type (SINGLE_TEST/PACKAGE), price, turnaround_time, includes (comma separated)
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV.")
        
    try:
        # 1. DO NOT use await file.read(). Use the underlying spooled file directly.
        # This streams the file in chunks natively.
        import codecs
        
        # 2. Wrap the spooled file in a text stream reader
        stream = codecs.iterdecode(file.file, 'utf-8-sig')
        csv_reader = csv.DictReader(stream)
        
        items_added = 0
        batch_size = 500 # Flush to DB in batches to maintain high speed
        
        for row in csv_reader:
            # Skip empty rows
            if not row.get('title') or not row.get('price'):
                continue
                
            # Process the 'includes' column (convert "CBC, FBS" into a JSON list)
            includes_data = []
            if row.get('includes'):
                includes_data = [item.strip() for item in row['includes'].split(',') if item.strip()]
                
            new_item = LabCatalogModel(
                type=row.get('type', 'SINGLE_TEST').upper(),
                title=row['title'].strip(),
                price=float(row['price']),
                turnaround_time=row.get('turnaround_time', '24 Hours').strip(),
                includes=includes_data,
                tenant_id=admin_user.tenant_id # Injecting multi-tenancy context invisibly
            )
            db.add(new_item)
            items_added += 1
            
            # Commit in chunks to avoid blocking the transaction log
            if items_added % batch_size == 0:
                db.commit()
                
        db.commit() # Final commit for remaining items
        return {"message": f"Successfully uploaded {items_added} lab tests to the catalog."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")
    finally:
        file.file.close() # Always close the spooled file

@router.post("/", response_model=LabCatalogSchema, status_code=status.HTTP_201_CREATED)
def create_lab_item(
    item: LabCatalogCreate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin Action: Add a new individual lab test or a full checkup package to the catalog.
    """
    return crud_lab_catalog.create_lab_item(db=db, item=item, context_tenant_id=admin_user.tenant_id)

@router.get("/", response_model=list[LabCatalogSchema])
def get_lab_catalog(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    return crud_lab_catalog.get_lab_items(db, skip=skip, limit=limit)

@router.get("/{item_id}", response_model=LabCatalogSchema)
def get_lab_item(
    item_id: UUID, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    db_item = crud_lab_catalog.get_lab_item(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Lab item not found")
    return db_item

@router.patch("/{item_id}", response_model=LabCatalogSchema)
def update_lab_item(
    item_id: UUID, 
    item_update: LabCatalogUpdate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin Action: Update pricing, turnaround time, or included tests for an existing catalog item.
    """
    db_item = crud_lab_catalog.get_lab_item(db, item_id=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Lab item not found"
        )
    
    return crud_lab_catalog.update_lab_item(db=db, db_item=db_item, item_update=item_update)

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lab_item(
    item_id: UUID, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin Action: Remove an item from the catalog entirely.
    """
    db_item = crud_lab_catalog.get_lab_item(db, item_id=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Lab item not found"
        )
    
    crud_lab_catalog.delete_lab_item(db=db, db_item=db_item)
    return None
