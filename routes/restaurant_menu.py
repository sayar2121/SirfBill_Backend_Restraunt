import os
import logging
import io
import csv

logger = logging.getLogger(__name__)
import uuid
from decimal import Decimal
import python_calamine
from fastapi import UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
import httpx
import re
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from models.database import get_db
from models.user import User
from models.restaurant_outlet import RestaurantOutlet
from models.restaurant_menu import RestaurantMenuCategory, RestaurantMenuItem, RestaurantItemPrice
from models.restaurant_modifier import RestaurantModifierGroup, RestaurantModifierOption, RestaurantItemModifierGroup
from schemas.restaurant_menu import (
    RestaurantMenuCategoryCreate, RestaurantMenuCategoryUpdate, RestaurantMenuCategoryResponse,
    RestaurantMenuItemCreate, RestaurantMenuItemUpdate, RestaurantMenuItemResponse
)
from schemas.restaurant_modifier import (
    RestaurantModifierGroupCreate, RestaurantModifierGroupResponse,
    RestaurantModifierOptionCreate, RestaurantModifierOptionResponse
)
from dependencies import get_current_user, get_restaurant_manager, get_restaurant_staff, get_optional_restaurant_staff

def generate_short_code(db: Session, outlet_id: UUID, name: str) -> str:
    """
    Generate an uppercase short code based on item name (e.g. 'Chicken Biryani' -> 'CB').
    Ensures uniqueness within the outlet by appending a numeric suffix if needed (e.g. 'CB2').
    """
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name).strip()
    words = cleaned.split()
    if not words:
        base_code = "ITEM"
    elif len(words) == 1:
        base_code = words[0][:4].upper()
    else:
        # Take initials of each word up to 4 characters
        base_code = "".join([w[0] for w in words[:4]]).upper()

    if not base_code:
        base_code = "ITM"

    candidate = base_code
    counter = 1
    while True:
        existing = db.query(RestaurantMenuItem).filter(
            RestaurantMenuItem.outlet_id == outlet_id,
            RestaurantMenuItem.short_code == candidate,
            RestaurantMenuItem.is_active == True
        ).first()
        if not existing:
            return candidate
        counter += 1
        candidate = f"{base_code}{counter}"

router = APIRouter(
    prefix="/api/restaurant/menu",
    tags=["Restaurant - Menu & Modifiers"]
)


# ----------------- MENU CATEGORIES -----------------

@router.get("/categories", response_model=List[RestaurantMenuCategoryResponse])
def get_menu_categories(
    outlet_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    if not outlet_id:
        first_outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.is_active == True).first()
        if not first_outlet:
            return []
        outlet_id = first_outlet.id

    return (
        db.query(RestaurantMenuCategory)
        .filter(RestaurantMenuCategory.outlet_id == outlet_id)
        .order_by(RestaurantMenuCategory.sort_order.asc())
        .all()
    )

@router.post("/categories", response_model=RestaurantMenuCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_menu_category(
    payload: RestaurantMenuCategoryCreate,
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    outlet = None
    if payload.outlet_id:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == payload.outlet_id).first()
    if not outlet:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.is_active == True).first()
    if not outlet:
        outlet = db.query(RestaurantOutlet).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Restaurant outlet not found")

    emoji = payload.icon_emoji or "🍽️"
    category = RestaurantMenuCategory(
        outlet_id=outlet.id,
        tenant_id=outlet.tenant_id,
        name=payload.name,
        description=payload.description,
        icon_emoji=emoji,
        sort_order=payload.sort_order,
        is_active=payload.is_active
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.put("/categories/{category_id}", response_model=RestaurantMenuCategoryResponse)
@router.patch("/categories/{category_id}", response_model=RestaurantMenuCategoryResponse)
def update_menu_category(
    category_id: UUID,
    payload: RestaurantMenuCategoryUpdate,
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    category = db.query(RestaurantMenuCategory).filter(RestaurantMenuCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    category = db.query(RestaurantMenuCategory).filter(RestaurantMenuCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Unlink items or delete category
    db.query(RestaurantMenuItem).filter(RestaurantMenuItem.category_id == category_id).update({"category_id": None})
    db.delete(category)
    db.commit()
    return None


# ----------------- MENU ITEMS -----------------

@router.get("/items", response_model=List[RestaurantMenuItemResponse])
def get_menu_items(
    outlet_id: Optional[UUID] = None,
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    available_only: bool = False,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    if not outlet_id:
        first_outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.is_active == True).first()
        if not first_outlet:
            return []
        outlet_id = first_outlet.id

    query = (
        db.query(RestaurantMenuItem)
        .options(joinedload(RestaurantMenuItem.prices))
        .filter(RestaurantMenuItem.outlet_id == outlet_id)
        .filter(RestaurantMenuItem.is_active == True)
    )
    if category_id:
        query = query.filter(RestaurantMenuItem.category_id == category_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                RestaurantMenuItem.name.ilike(term),
                RestaurantMenuItem.short_code.ilike(term)
            )
        )
    if available_only:
        query = query.filter(RestaurantMenuItem.is_available == True)

    return query.all()

@router.post("/items", response_model=RestaurantMenuItemResponse, status_code=status.HTTP_201_CREATED)
def create_menu_item(
    payload: RestaurantMenuItemCreate,
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    outlet = None
    if payload.outlet_id:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == payload.outlet_id).first()
    if not outlet:
        outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.is_active == True).first()
    if not outlet:
        outlet = db.query(RestaurantOutlet).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="No active restaurant outlet found.")

    # Determine item_type from is_veg or item_type
    item_type = payload.item_type or "NON_VEG"
    if payload.is_veg is not None:
        item_type = "VEG" if payload.is_veg else "NON_VEG"

    # Category UUID resolution (slug vs UUID)
    resolved_category_id = None
    if payload.category_id:
        try:
            resolved_category_id = UUID(str(payload.category_id))
        except (ValueError, TypeError):
            # Lookup category by name or create it
            cat_name = str(payload.category_id).title()
            cat = db.query(RestaurantMenuCategory).filter(
                RestaurantMenuCategory.outlet_id == outlet.id,
                RestaurantMenuCategory.name.ilike(cat_name)
            ).first()
            if not cat:
                cat = RestaurantMenuCategory(
                    outlet_id=outlet.id,
                    tenant_id=outlet.tenant_id,
                    name=cat_name,
                    is_active=True
                )
                db.add(cat)
                db.flush()
            resolved_category_id = cat.id

    # Auto-generate short_code if not supplied
    short_code = payload.short_code.strip().upper() if payload.short_code and payload.short_code.strip() else None
    if not short_code:
        short_code = generate_short_code(db, outlet.id, payload.name)

    item = RestaurantMenuItem(
        outlet_id=outlet.id,
        tenant_id=outlet.tenant_id,
        category_id=resolved_category_id,
        name=payload.name,
        short_code=short_code,
        description=payload.description,
        image_url=payload.image_url,
        item_type=item_type,
        prep_station=payload.prep_station or "KITCHEN",
        tax_rate=payload.tax_rate or Decimal("5.00"),
        price=payload.price or Decimal("0.00"),
        badge=payload.badge,
        is_available=payload.is_available,
        is_active=payload.is_active
    )
    db.add(item)
    db.flush()

    # Add standard base price to prices table as well for variant compatibility
    base_price = payload.price or Decimal("0.00")
    if not payload.prices:
        db_price = RestaurantItemPrice(
            item_id=item.id,
            variant_name="Standard",
            channel="DEFAULT",
            price=base_price
        )
        db.add(db_price)
    else:
        for p in payload.prices:
            db_price = RestaurantItemPrice(
                item_id=item.id,
                variant_name=p.variant_name,
                channel=p.channel,
                price=p.price
            )
            db.add(db_price)

    # Add modifier group associations
    for grp_id in payload.modifier_group_ids:
        link = RestaurantItemModifierGroup(
            item_id=item.id,
            modifier_group_id=grp_id
        )
        db.add(link)

    db.commit()
    db.refresh(item)
    return item

@router.put("/items/{item_id}", response_model=RestaurantMenuItemResponse)
@router.patch("/items/{item_id}", response_model=RestaurantMenuItemResponse)
def update_menu_item(
    item_id: UUID,
    payload: RestaurantMenuItemUpdate,
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    item = db.query(RestaurantMenuItem).filter(RestaurantMenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    dump = payload.model_dump(exclude_unset=True)

    # Handle veg / non-veg mapping
    if "is_veg" in dump and dump["is_veg"] is not None:
        item.item_type = "VEG" if dump["is_veg"] else "NON_VEG"
    elif "item_type" in dump and dump["item_type"]:
        item.item_type = dump["item_type"]

    # Handle category resolution
    if "category_id" in dump and dump["category_id"]:
        try:
            item.category_id = UUID(str(dump["category_id"]))
        except (ValueError, TypeError):
            cat_name = str(dump["category_id"]).title()
            cat = db.query(RestaurantMenuCategory).filter(
                RestaurantMenuCategory.outlet_id == item.outlet_id,
                RestaurantMenuCategory.name.ilike(cat_name)
            ).first()
            if not cat:
                cat = RestaurantMenuCategory(
                    outlet_id=item.outlet_id,
                    tenant_id=item.tenant_id,
                    name=cat_name,
                    is_active=True
                )
                db.add(cat)
                db.flush()
            item.category_id = cat.id

    # Handle price update if supplied
    if "price" in dump and dump["price"] is not None:
        item.price = dump["price"]
        price_rec = db.query(RestaurantItemPrice).filter(
            RestaurantItemPrice.item_id == item.id,
            RestaurantItemPrice.channel == "DEFAULT"
        ).first()
        if price_rec:
            price_rec.price = dump["price"]
        else:
            new_price = RestaurantItemPrice(
                item_id=item.id,
                variant_name="Standard",
                channel="DEFAULT",
                price=dump["price"]
            )
            db.add(new_price)

    # Set remaining fields
    standard_fields = ["name", "short_code", "description", "image_url", "badge", "prep_station", "tax_rate", "is_available", "is_active"]
    for field in standard_fields:
        if field in dump and dump[field] is not None:
            val = dump[field]
            if field == "short_code" and isinstance(val, str):
                val = val.strip().upper()
            setattr(item, field, val)

    if not item.short_code and item.name:
        item.short_code = generate_short_code(db, item.outlet_id, item.name)

    db.commit()
    db.refresh(item)
    return item

@router.patch("/items/{item_id}/availability", response_model=RestaurantMenuItemResponse)
def toggle_menu_item_availability(
    item_id: UUID,
    payload: dict,
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    item = db.query(RestaurantMenuItem).filter(RestaurantMenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if "is_available" in payload:
        item.is_available = bool(payload["is_available"])

    db.commit()
    db.refresh(item)
    return item

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    manager_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    item = db.query(RestaurantMenuItem).filter(RestaurantMenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    db.delete(item)
    db.commit()
    return None


# ----------------- MODIFIER GROUPS -----------------

@router.get("/modifier-groups", response_model=List[RestaurantModifierGroupResponse])
def get_modifier_groups(
    outlet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_restaurant_staff)
):
    return (
        db.query(RestaurantModifierGroup)
        .options(joinedload(RestaurantModifierGroup.options))
        .filter(RestaurantModifierGroup.outlet_id == outlet_id)
        .filter(RestaurantModifierGroup.is_active == True)
        .all()
    )

@router.post("/modifier-groups", response_model=RestaurantModifierGroupResponse, status_code=status.HTTP_201_CREATED)
def create_modifier_group(
    payload: RestaurantModifierGroupCreate,
    db: Session = Depends(get_db),
    manager_user: User = Depends(get_restaurant_manager)
):
    outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == payload.outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Restaurant outlet not found")

    group = RestaurantModifierGroup(
        outlet_id=payload.outlet_id,
        tenant_id=outlet.tenant_id,
        name=payload.name,
        description=payload.description,
        min_selection=payload.min_selection,
        max_selection=payload.max_selection,
        is_active=payload.is_active
    )
    db.add(group)
    db.flush()

    for opt in payload.options:
        db_opt = RestaurantModifierOption(
            group_id=group.id,
            name=opt.name,
            price_delta=opt.price_delta,
            is_available=opt.is_available,
            is_active=opt.is_active
        )
        db.add(db_opt)

    db.commit()
    db.refresh(group)
    return group


# ----------------- BULK UPLOAD & TEMPLATE -----------------

@router.get("/sample-template")
def download_sample_menu_template(
    outlet_id: Optional[UUID] = Query(None),
    format: str = Query("xlsx"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    """
    Download clean, BLANK outlet-specific template with in-cell dropdowns
    for Category (outlet-specific), Type (VEG/NON_VEG), Prep Station, and Availability.
    Zero pre-filled dishes - completely blank for user input.
    """
    # 1. Resolve Target Outlet
    target_outlet = None
    if outlet_id:
        target_outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == outlet_id).first()
    if not target_outlet and current_user and current_user.outlet_id:
        target_outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == current_user.outlet_id).first()
    if not target_outlet:
        target_outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.is_active == True).first() or db.query(RestaurantOutlet).first()

    outlet_name = target_outlet.name if target_outlet else "Restaurant"
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', outlet_name).strip('_').lower()

    # 2. Fetch categories belonging specifically to this outlet
    categories = []
    if target_outlet:
        db_cats = db.query(RestaurantMenuCategory).filter(
            RestaurantMenuCategory.outlet_id == target_outlet.id,
            RestaurantMenuCategory.is_active == True
        ).order_by(RestaurantMenuCategory.name).all()
        categories = [c.name.strip() for c in db_cats if c.name and c.name.strip()]

    if not categories:
        categories = ["Main Course", "Starters", "Biryani", "Tandoor", "Breads", "Desserts", "Beverages"]

    # Remove duplicates preserving order
    seen = set()
    unique_categories = []
    for c in categories:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique_categories.append(c)
    categories = unique_categories

    # 3. Generate XLSX with In-Cell Dropdowns via openpyxl
    if format.lower() == "xlsx":
        import openpyxl
        from openpyxl.worksheet.datavalidation import DataValidation
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Menu Items"

        # Headers
        headers = [
            "Item Name", "Category", "Price", "Type", "Short Code",
            "Description", "Prep Station", "Tax Rate", "Badge", "Image URL", "Is Available"
        ]
        ws.append(headers)

        header_fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_align
        ws.row_dimensions[1].height = 28

        # Generous column widths so cells are spacious and readable
        col_widths = {
            "A": 30, # Item Name
            "B": 24, # Category
            "C": 14, # Price
            "D": 18, # Type
            "E": 16, # Short Code
            "F": 38, # Description
            "G": 18, # Prep Station
            "H": 14, # Tax Rate
            "I": 16, # Badge
            "J": 20, # Image URL
            "K": 16, # Is Available
        }
        for col_letter, width in col_widths.items():
            ws.column_dimensions[col_letter].width = width

        # Optional second visible sheet listing Categories & Options for reference
        ws_lookup = wb.create_sheet(title="Categories & Options")
        lookup_header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
        lookup_headers = ["Available Categories", "Item Types", "Prep Stations", "Availability"]
        ws_lookup.append(lookup_headers)
        for col_idx in range(1, len(lookup_headers) + 1):
            c_cell = ws_lookup.cell(row=1, column=col_idx)
            c_cell.fill = lookup_header_fill
            c_cell.font = header_font
            c_cell.alignment = header_align
        ws_lookup.row_dimensions[1].height = 24

        types = ["VEG", "NON_VEG", "EGG", "VEGAN"]
        stations = ["KITCHEN", "BAR", "DESSERT", "PANTRY"]
        availabilities = ["TRUE", "FALSE"]

        max_rows = max(len(categories), len(types), len(stations), len(availabilities))
        for r in range(max_rows):
            ws_lookup.append([
                categories[r] if r < len(categories) else "",
                types[r] if r < len(types) else "",
                stations[r] if r < len(stations) else "",
                availabilities[r] if r < len(availabilities) else ""
            ])
        ws_lookup.column_dimensions["A"].width = 26
        ws_lookup.column_dimensions["B"].width = 16
        ws_lookup.column_dimensions["C"].width = 18
        ws_lookup.column_dimensions["D"].width = 16

        # NOTE: NO SAMPLE DATA ROWS IN "Menu Items" - COMPLETELY BLANK TEMPLATE!

        # 4. In-cell Dropdown Data Validations (Direct string literals compatible with Google Sheets & Excel)
        # Dropdown 1: Category on Column B
        cat_str = ",".join(categories)
        if len(cat_str) <= 250:
            dv_cat = DataValidation(type="list", formula1=f'"{cat_str}"', allow_blank=True)
        else:
            dv_cat = DataValidation(type="list", formula1=f"='Categories & Options'!$A$2:$A${len(categories) + 1}", allow_blank=True)
        dv_cat.showDropDown = None
        ws.add_data_validation(dv_cat)
        dv_cat.add("B2:B500")

        # Dropdown 2: Type on Column D (VEG, NON_VEG, EGG, VEGAN)
        dv_type = DataValidation(type="list", formula1='"VEG,NON_VEG,EGG,VEGAN"', allow_blank=True)
        dv_type.showDropDown = None
        ws.add_data_validation(dv_type)
        dv_type.add("D2:D500")

        # Dropdown 3: Prep Station on Column G
        dv_station = DataValidation(type="list", formula1='"KITCHEN,BAR,DESSERT,PANTRY"', allow_blank=True)
        dv_station.showDropDown = None
        ws.add_data_validation(dv_station)
        dv_station.add("G2:G500")

        # Dropdown 4: Is Available on Column K (TRUE, FALSE)
        dv_avail = DataValidation(type="list", formula1='"TRUE,FALSE"', allow_blank=True)
        dv_avail.showDropDown = None
        ws.add_data_validation(dv_avail)
        dv_avail.add("K2:K500")

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"menu_template_{slug}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    # 4. CSV Fallback: Blank header row only
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Item Name", "Category", "Price", "Type", "Short Code", 
        "Description", "Prep Station", "Tax Rate", "Badge", "Image URL", "Is Available"
    ])
    
    output.seek(0)
    filename = f"menu_template_{slug}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/bulk-upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload_menu_items(
    file: UploadFile = File(...),
    outlet_id: Optional[UUID] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    """
    Bulk Upload Menu Items from Excel (.xlsx, .xls) or CSV.
    - uid=501(sayarpaul) gid=20(staff) groups=20(staff),12(everyone),61(localaccounts),79(_appserverusr),80(admin),81(_appserveradm),701(com.apple.sharepoint.group.1),33(_appstore),98(_lpadmin),100(_lpoperator),204(_developer),250(_analyticsusers),395(com.apple.access_ftp),398(com.apple.access_screensharing),399(com.apple.access_ssh),400(com.apple.access_remote_ae): Auto-generated UUID for every dish.
    - : Guessed/inferred from request, active user outlet, or fallback active outlet.
    - : Inferred automatically from the outlet.
    - : Auto-creates category if it does not already exist for this outlet.
    - : Auto-generated based on dish name if not supplied or blank.
    """
    filename = (file.filename or '').lower()
    if not (filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv')):
        raise HTTPException(
            status_code=400, 
            detail="Only Excel (.xlsx, .xls) and CSV files are supported for bulk menu upload."
        )

    # 1. Resolve Target Outlet & Tenant
    target_outlet = None
    if outlet_id:
        target_outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == outlet_id).first()
    
    if not target_outlet and current_user and current_user.outlet_id:
        target_outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == current_user.outlet_id).first()
        
    if not target_outlet:
        target_outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.is_active == True).first() or db.query(RestaurantOutlet).first()

    if not target_outlet:
        raise HTTPException(status_code=404, detail="No active restaurant outlet found to assign menu items.")

    resolved_outlet_id = target_outlet.id
    resolved_tenant_id = target_outlet.tenant_id or (current_user.tenant_id if current_user else None) or target_outlet.id

    # 2. Parse File Rows
    try:
        content = await file.read()
        file_bytes = io.BytesIO(content)

        if filename.endswith('.csv'):
            decoded = content.decode('utf-8-sig', errors='ignore').splitlines()
            reader = csv.reader(decoded)
            rows = [row for row in reader if any(field.strip() for field in row)]
        else:
            workbook = python_calamine.CalamineWorkbook.from_filelike(file_bytes)
            sheet_name = workbook.sheet_names[0]
            rows = workbook.get_sheet_by_name(sheet_name).to_python(skip_empty_area=True)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if not rows or len(rows) < 2:
        raise HTTPException(status_code=400, detail="The file is empty or missing data rows.")

    header_row = [str(cell).strip().lower() for cell in rows[0]]
    data_rows = rows[1:]

    # Map header column names flexibly
    col_map = {}
    for idx, col in enumerate(header_row):
        clean = "".join(c if c.isalnum() else "_" for c in col).strip("_")
        while "__" in clean:
            clean = clean.replace("__", "_")
        
        if clean in ["name", "dish_name", "item_name", "food_name", "item", "dish"]:
            col_map["name"] = idx
        elif clean in ["category", "category_name", "cat", "group", "menu_category"]:
            col_map["category"] = idx
        elif clean in ["price", "mrp", "selling_price", "rate", "cost", "amount"]:
            col_map["price"] = idx
        elif clean in ["type", "item_type", "food_type", "dietary", "is_veg", "veg_non_veg", "veg_or_non_veg"]:
            col_map["item_type"] = idx
        elif clean in ["short_code", "code", "item_code", "shortcode"]:
            col_map["short_code"] = idx
        elif clean in ["description", "desc", "details"]:
            col_map["description"] = idx
        elif clean in ["prep_station", "station", "kitchen_station"]:
            col_map["prep_station"] = idx
        elif clean in ["tax_rate", "tax", "gst", "gst_rate"]:
            col_map["tax_rate"] = idx
        elif clean in ["badge", "tag"]:
            col_map["badge"] = idx
        elif clean in ["image_url", "image", "photo", "img"]:
            col_map["image_url"] = idx
        elif clean in ["is_available", "available", "in_stock"]:
            col_map["is_available"] = idx

    if "name" not in col_map:
        raise HTTPException(
            status_code=400, 
            detail="Header must contain a column for dish name (e.g. 'Item Name' or 'name')."
        )

    # 3. Cache existing categories for this outlet to minimize DB queries
    existing_categories = {
        c.name.strip().lower(): c 
        for c in db.query(RestaurantMenuCategory).filter(
            RestaurantMenuCategory.outlet_id == resolved_outlet_id
        ).all()
    }

    created_items_count = 0
    updated_items_count = 0
    created_categories_count = 0

    for row_idx, row in enumerate(data_rows, start=2):
        if not row or all(str(c).strip() == "" for c in row):
            continue

        def get_val(key, default=""):
            idx = col_map.get(key)
            if idx is not None and idx < len(row):
                val = row[idx]
                if val is not None:
                    return str(val).strip()
            return default

        dish_name = get_val("name")
        if not dish_name:
            continue

        raw_category = get_val("category", "Main Course").strip()
        cat_key = raw_category.lower()

        # Handle category: auto-create if not found
        category_obj = existing_categories.get(cat_key)
        if not category_obj:
            category_obj = RestaurantMenuCategory(
                id=uuid.uuid4(),
                outlet_id=resolved_outlet_id,
                tenant_id=resolved_tenant_id,
                name=raw_category.title(),
                icon_emoji="🍽️",
                is_active=True
            )
            db.add(category_obj)
            db.flush()
            existing_categories[cat_key] = category_obj
            created_categories_count += 1

        # Parse price
        raw_price = get_val("price", "0")
        try:
            cleaned_price = re.sub(r'[^\d.]', '', raw_price)
            price_val = Decimal(cleaned_price) if cleaned_price else Decimal("0.00")
        except Exception:
            price_val = Decimal("0.00")

        # Parse item_type (VEG, NON_VEG, EGG, VEGAN)
        raw_type = get_val("item_type", "").upper()
        if any(v in raw_type for v in ["NON", "NV", "CHICKEN", "MUTTON", "FISH", "MEAT"]):
            item_type = "NON_VEG"
        elif "EGG" in raw_type:
            item_type = "EGG"
        elif "VEGAN" in raw_type:
            item_type = "VEGAN"
        elif any(v in raw_type for v in ["VEG", "V", "YES", "TRUE"]):
            item_type = "VEG"
        else:
            item_type = "NON_VEG"

        # Short Code: auto-generated if missing or empty
        provided_code = get_val("short_code")
        if provided_code:
            short_code = re.sub(r'[^a-zA-Z0-9]', '', provided_code).upper()[:20]
        else:
            short_code = generate_short_code(db, resolved_outlet_id, dish_name)

        # Tax rate
        raw_tax = get_val("tax_rate", "5.0")
        try:
            cleaned_tax = re.sub(r'[^\d.]', '', raw_tax)
            tax_rate = Decimal(cleaned_tax) if cleaned_tax else Decimal("5.00")
        except Exception:
            tax_rate = Decimal("5.00")

        # Prep station
        prep_station = get_val("prep_station", "KITCHEN").upper() or "KITCHEN"

        # Availability
        raw_avail = get_val("is_available", "TRUE").lower()
        is_available = raw_avail not in ["false", "no", "0", "out_of_stock"]

        # Description, Badge, Image
        description = get_val("description") or None
        badge = get_val("badge") or None
        image_url = get_val("image_url") or None

        # Check if item with this name already exists in this outlet
        existing_item = db.query(RestaurantMenuItem).filter(
            RestaurantMenuItem.outlet_id == resolved_outlet_id,
            RestaurantMenuItem.name.ilike(dish_name),
            RestaurantMenuItem.is_active == True
        ).first()

        if existing_item:
            # Update existing item
            existing_item.category_id = category_obj.id
            existing_item.price = price_val
            existing_item.item_type = item_type
            if provided_code:
                existing_item.short_code = short_code
            if description:
                existing_item.description = description
            if badge:
                existing_item.badge = badge
            if image_url:
                existing_item.image_url = image_url
            existing_item.prep_station = prep_station
            existing_item.tax_rate = tax_rate
            existing_item.is_available = is_available
            
            # Update default price record
            default_price = db.query(RestaurantItemPrice).filter(
                RestaurantItemPrice.item_id == existing_item.id,
                RestaurantItemPrice.channel == "DEFAULT"
            ).first()
            if default_price:
                default_price.price = price_val
            else:
                db.add(RestaurantItemPrice(
                    id=uuid.uuid4(),
                    item_id=existing_item.id,
                    variant_name="Standard",
                    channel="DEFAULT",
                    price=price_val
                ))
            updated_items_count += 1
        else:
            # Create new menu item with auto-generated UUID
            new_item_id = uuid.uuid4()
            new_item = RestaurantMenuItem(
                id=new_item_id,
                outlet_id=resolved_outlet_id,
                tenant_id=resolved_tenant_id,
                category_id=category_obj.id,
                name=dish_name,
                short_code=short_code,
                description=description,
                image_url=image_url,
                item_type=item_type,
                prep_station=prep_station,
                tax_rate=tax_rate,
                price=price_val,
                badge=badge,
                is_available=is_available,
                is_active=True
            )
            db.add(new_item)
            db.flush()

            # Create default standard price
            db.add(RestaurantItemPrice(
                id=uuid.uuid4(),
                item_id=new_item.id,
                variant_name="Standard",
                channel="DEFAULT",
                price=price_val
            ))
            created_items_count += 1

    db.commit()

    return {
        "success": True,
        "outlet_id": str(resolved_outlet_id),
        "outlet_name": target_outlet.name,
        "created_count": created_items_count,
        "updated_count": updated_items_count,
        "categories_created": created_categories_count,
        "total_processed": created_items_count + updated_items_count,
        "message": f"Successfully processed {created_items_count + updated_items_count} menu items for {target_outlet.name}."
    }


FALLBACK_FOOD_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <rect width="100%" height="100%" fill="#1e293b"/>
  <circle cx="200" cy="130" r="55" fill="#334155"/>
  <path d="M175 140c0-14 11-25 25-25s25 11 25 25v5h-50v-5z" fill="#10b981"/>
  <path d="M165 150h70v5h-70z" fill="#10b981"/>
  <circle cx="200" cy="110" r="5" fill="#10b981"/>
  <text x="200" y="225" font-family="sans-serif" font-size="16" font-weight="bold" fill="#94a3b8" text-anchor="middle">SirfBill Restaurant</text>
</svg>"""

IMAGE_CACHE_DIR = os.path.join("uploads", "cache")
os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)


@router.api_route("/image-proxy", methods=["GET", "HEAD"])
async def image_proxy(url: str = Query(...)):
    """
    Proxy image requests to bypass browser CORS restrictions and cache images on disk.
    If upstream times out or is unreachable, serves a clean placeholder image rather than a 500 error.
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    import hashlib
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    cache_path = os.path.join(IMAGE_CACHE_DIR, f"{url_hash}.bin")
    meta_path = os.path.join(IMAGE_CACHE_DIR, f"{url_hash}.meta")

    # Serve from disk cache if already downloaded
    if os.path.exists(cache_path) and os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as mf:
                content_type = mf.read().strip() or "image/jpeg"
            with open(cache_path, "rb") as cf:
                cached_data = cf.read()
            return Response(
                content=cached_data,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=604800, immutable",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        except Exception:
            pass

    try:
        # Fast 4-second connect timeout so upstream ISP/CDN routing hangs don't stall clients
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(connect=4.0, read=8.0, write=4.0, pool=4.0)
        ) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            }
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200 and resp.content:
                content_type = resp.headers.get("content-type", "image/jpeg")
                # Save to disk cache
                try:
                    with open(cache_path, "wb") as cf:
                        cf.write(resp.content)
                    with open(meta_path, "w", encoding="utf-8") as mf:
                        mf.write(content_type)
                except Exception:
                    pass

                return Response(
                    content=resp.content,
                    media_type=content_type,
                    headers={
                        "Cache-Control": "public, max-age=604800, immutable",
                        "Access-Control-Allow-Origin": "*",
                    }
                )
    except Exception as e:
        logger.warning(f"image_proxy upstream fetch error for {url}: {e}")

    # Return placeholder SVG so frontend displays a clean placeholder without breaking or logging 500s
    return Response(
        content=FALLBACK_FOOD_SVG.encode("utf-8"),
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Access-Control-Allow-Origin": "*",
        }
    )

