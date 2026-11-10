from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import python_calamine # Fast Rust-based Excel parser

from models.database import get_db
from dependencies import get_admin_user
from models.user import User
from models.inventory import InventoryItem
from models.shop import Shop
from schemas.shop import ShopCreate, ShopResponse, ShopUpdate
from schemas.inventory import InventoryItemCreate, InventoryItemUpdate
from models.rack import Rack
from schemas.rack import RackCreate, RackUpdate, RackOut as RackSchema
from models.category import Category
from schemas.category import CategoryCreate, CategoryUpdate, CategoryOut as CategorySchema
from models.distributor import Distributor
from sqlalchemy import or_, cast, String
from typing import List, Optional

router = APIRouter(
    prefix="/api/admin/shop",
    tags=["Admin - Pharmacy & Inventory"]
)

@router.post("", response_model=ShopResponse, status_code=status.HTTP_201_CREATED)
async def create_shop(
    request: ShopCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: Create a new restaurant outlet/shop, saving all 5 configuration sections.
    """
    tenant_id = admin_user.tenant_id
    # Collect extra data both from extra_data dictionary and from top-level dynamic keys passed by Flutter
    extra = dict(request.extra_data or {})
    if hasattr(request, "model_extra") and request.model_extra:
        extra.update(request.model_extra)

    # Resolve all fields flexibly whether nested or flat
    address_val = extra.get("address_line1") or request.address or ""
    if extra.get("address_line2"):
        address_val = f"{address_val}, {extra.get('address_line2')}".strip(", ")
    if not address_val:
        address_val = request.address or ""

    city_val = extra.get("city") or request.city or ""
    state_val = extra.get("state") or ""
    pin_val = extra.get("pin_code") or ""
    country_val = extra.get("country") or "India"
    phone_val = extra.get("contact_number") or request.contact_number or ""
    email_val = extra.get("email") or ""
    outlet_type_val = extra.get("outlet_type") or "Dine-in, Takeaway & Delivery"
    gstin_val = extra.get("gstin") or extra.get("billing_tax", {}).get("gstin", "")
    fssai_val = extra.get("fssai") or extra.get("billing_tax", {}).get("fssai", "")
    prefix_val = extra.get("invoice_prefix") or extra.get("billing_tax", {}).get("invoice_prefix", "ORD-")
    try:
        tax_val = float(extra.get("tax_rate") or extra.get("billing_tax", {}).get("tax_rate", 5.0))
    except (ValueError, TypeError):
        tax_val = 5.0
    open_time_val = extra.get("opening_time") or extra.get("operating_settings", {}).get("opening_time", "09:00 AM")
    close_time_val = extra.get("closing_time") or extra.get("operating_settings", {}).get("closing_time", "11:00 PM")
    weekly_close_val = extra.get("weekly_closing") or extra.get("operating_settings", {}).get("weekly_closing", "None (Open 7 Days)")
    desc_val = extra.get("description") or ""

    # 1. Generate clean module login credentials for this outlet matching the Flutter UI
    safe_code = (request.code or "outlet").lower().replace("-", "").replace(" ", "")
    default_pass = "123456"

    module_accounts = extra.get("module_accounts") or {
        "pos": {
            "name": f"{request.name} POS Cashier",
            "username": f"{safe_code}_pos",
            "password": default_pass,
            "role": "CASHIER"
        },
        "kitchen": {
            "name": f"{request.name} Kitchen Display",
            "username": f"{safe_code}_kds",
            "password": default_pass,
            "role": "KITCHEN"
        },
        "inventory": {
            "name": f"{request.name} Inventory & Purchase",
            "username": f"{safe_code}_inv",
            "password": default_pass,
            "role": "MANAGER"
        },
        "crm": {
            "name": f"{request.name} CRM & Reports",
            "username": f"{safe_code}_crm",
            "password": default_pass,
            "role": "MANAGER"
        },
        "waiter": {
            "name": f"{request.name} Waiter / Captain",
            "username": f"{safe_code}_waiter",
            "password": default_pass,
            "role": "WAITER"
        }
    }
    extra["module_accounts"] = module_accounts

    # 1. Create or persist in RestaurantOutlet with both SQL columns and service_settings
    new_outlet = RestaurantOutlet(
        tenant_id=tenant_id,
        name=request.name,
        code=request.code,
        timezone=extra.get("time_zone") or extra.get("operating_settings", {}).get("time_zone", "Asia/Kolkata"),
        currency=extra.get("currency") or extra.get("operating_settings", {}).get("currency", "INR"),
        address=address_val,
        city=city_val,
        state=state_val,
        pin_code=pin_val,
        country=country_val,
        phone=phone_val,
        email=email_val,
        outlet_type=outlet_type_val,
        gstin=gstin_val,
        fssai=fssai_val,
        invoice_prefix=prefix_val,
        tax_rate=tax_val,
        opening_time=open_time_val,
        closing_time=close_time_val,
        weekly_closing=weekly_close_val,
        description=desc_val,
        logo_url=extra.get("logo_url"),
        upi_id=extra.get("upi_id") or extra.get("billing_tax", {}).get("upi_id", ""),
        bank_name=extra.get("bank_name"),
        bank_account_no=extra.get("bank_account_no") or extra.get("ac_number"),
        bank_ifsc=extra.get("bank_ifsc") or extra.get("ifsc_code"),
        bank_branch=extra.get("bank_branch") or extra.get("branch_name"),
        bank_account_name=extra.get("bank_account_name") or extra.get("ac_holder_name") or extra.get("account_holder_name") or request.account_holder_name,
        service_settings={
            "phone": phone_val,
            "address": address_val,
            "city": city_val,
            "state": state_val,
            "pin_code": pin_val,
            "country": country_val,
            "email": email_val,
            "outlet_type": outlet_type_val,
            "gstin": gstin_val,
            "fssai": fssai_val,
            "invoice_prefix": prefix_val,
            "tax_rate": tax_val,
            "opening_time": open_time_val,
            "closing_time": close_time_val,
            "weekly_closing": weekly_close_val,
            "description": desc_val,
            "logo_url": extra.get("logo_url"),
            "upi_id": extra.get("upi_id") or extra.get("billing_tax", {}).get("upi_id", ""),
            "bank_name": extra.get("bank_name"),
            "bank_account_no": extra.get("bank_account_no") or extra.get("ac_number"),
            "bank_ifsc": extra.get("bank_ifsc") or extra.get("ifsc_code"),
            "bank_branch": extra.get("bank_branch") or extra.get("branch_name"),
            "bank_account_name": extra.get("bank_account_name") or extra.get("ac_holder_name") or extra.get("account_holder_name") or request.account_holder_name,
            "account_holder_name": extra.get("bank_account_name") or extra.get("ac_holder_name") or extra.get("account_holder_name") or request.account_holder_name,
            "is_primary": request.is_primary,
            "extra_data": extra,
            "module_accounts": module_accounts,
            "dine_in_enabled": extra.get("enable_dine_in", True),
            "takeaway_enabled": extra.get("enable_takeaway", True),
            "delivery_enabled": extra.get("enable_delivery", True),
            "gst_number": gstin_val,
        },
        is_active=(request.status != "Inactive")
    )
    db.add(new_outlet)
    db.flush() # Generates new_outlet.id

    # Create / sync users in DB for each module (plain text as requested by user)
    for mod_key, creds in module_accounts.items():
        uname = creds.get("username")
        upass = creds.get("password")
        urole = creds.get("role", "CASHIER")
        uname_label = creds.get("name", f"{request.name} {mod_key.upper()}")
        existing_u = db.query(User).filter(User.email == uname).first()
        if not existing_u:
            new_u = User(
                tenant_id=tenant_id,
                outlet_id=new_outlet.id,
                email=uname,
                name=uname_label,
                phone=phone_val or "9999999999",
                role=urole,
                password=upass,
                is_active=True
            )
            db.add(new_u)
        else:
            existing_u.password = upass
            existing_u.role = urole
            existing_u.outlet_id = new_outlet.id

    # 2. Also persist in Shop table for backward compatibility
    new_shop = Shop(
        id=new_outlet.id,
        tenant_id=tenant_id,
        name=request.name,
        code=request.code,
        address=address_val or request.address,
        city=city_val or request.city,
        contact_number=phone_val or request.contact_number,
        account_holder_name=extra.get("bank_account_name") or extra.get("ac_holder_name") or extra.get("account_holder_name") or request.account_holder_name,
        status=request.status or "Active",
        is_primary=request.is_primary or False
    )
    db.add(new_shop)
    db.commit()
    db.refresh(new_outlet)

    resp = ShopResponse(
        id=new_outlet.id,
        tenant_id=tenant_id,
        name=new_outlet.name,
        code=new_outlet.code,
        address=new_outlet.address or request.address,
        city=new_outlet.city or request.city,
        contact_number=new_outlet.phone or request.contact_number,
        status="Active" if new_outlet.is_active else "Inactive",
        is_primary=request.is_primary or False,
        created_at=new_outlet.created_at,
        extra_data=extra
    )
    return resp

from dependencies import get_admin_user, get_optional_admin_user
from models.restaurant_outlet import RestaurantOutlet

@router.get("s", response_model=List[ShopResponse])
async def get_shops(
    db: Session = Depends(get_db),
    admin_user: Optional[User] = Depends(get_optional_admin_user)
):
    """
    Admin Action: Get all shops/outlets for the current tenant with all 5 sections.
    """
    query = db.query(RestaurantOutlet)
    if admin_user and admin_user.outlet_id and (not admin_user.role or admin_user.role.upper() not in ['ADMIN', 'OWNER', 'SUPER_ADMIN']):
        query = query.filter(RestaurantOutlet.id == admin_user.outlet_id)
    outlets = query.all()
    if outlets:
        results = []
        for o in outlets:
            svc = o.service_settings or {}
            extra = dict(svc.get("extra_data") or {})
            
            # Enrich extra with real database columns
            extra["outlet_type"] = o.outlet_type or extra.get("outlet_type")
            extra["address_line1"] = o.address or extra.get("address_line1")
            extra["city"] = o.city or extra.get("city")
            extra["state"] = o.state or extra.get("state")
            extra["pin_code"] = o.pin_code or extra.get("pin_code")
            extra["country"] = o.country or extra.get("country")
            extra["contact_number"] = o.phone or extra.get("contact_number")
            extra["email"] = o.email or extra.get("email")
            extra["gstin"] = o.gstin or extra.get("gstin")
            extra["fssai"] = o.fssai or extra.get("fssai")
            extra["invoice_prefix"] = o.invoice_prefix or extra.get("invoice_prefix")
            extra["tax_rate"] = float(o.tax_rate) if o.tax_rate is not None else extra.get("tax_rate", 5.0)
            extra["opening_time"] = o.opening_time or extra.get("opening_time")
            extra["closing_time"] = o.closing_time or extra.get("closing_time")
            extra["weekly_closing"] = o.weekly_closing or extra.get("weekly_closing")
            extra["description"] = o.description or extra.get("description")
            extra["time_zone"] = o.timezone or extra.get("time_zone")
            extra["currency"] = o.currency or extra.get("currency")
            extra["logo_url"] = o.logo_url or extra.get("logo_url")
            extra["upi_id"] = o.upi_id or extra.get("upi_id")
            extra["bank_name"] = o.bank_name or extra.get("bank_name")
            extra["bank_account_no"] = o.bank_account_no or extra.get("bank_account_no") or extra.get("ac_number")
            extra["bank_ifsc"] = o.bank_ifsc or extra.get("bank_ifsc") or extra.get("ifsc_code")
            extra["bank_branch"] = o.bank_branch or extra.get("bank_branch") or extra.get("branch_name")
            extra["bank_account_name"] = o.bank_account_name or extra.get("bank_account_name") or extra.get("ac_holder_name")
            extra["account_holder_name"] = extra["bank_account_name"]
            if "module_accounts" in svc:
                extra["module_accounts"] = svc["module_accounts"]

            results.append(ShopResponse(
                id=o.id,
                tenant_id=o.tenant_id,
                name=o.name,
                code=o.code or "OUTLET-1",
                address=o.address or svc.get("address", "Main Branch"),
                city=o.city or svc.get("city", "Main City"),
                contact_number=o.phone or svc.get("phone", ""),
                status="Active" if o.is_active else "Inactive",
                is_primary=svc.get("is_primary", False),
                account_holder_name=o.bank_account_name or extra.get("bank_account_name") or extra.get("ac_holder_name"),
                created_at=o.created_at,
                extra_data=extra
            ))
        return results

    # Fallback to Shop table if any
    query = db.query(Shop)
    if admin_user and admin_user.tenant_id:
        query = query.filter(Shop.tenant_id == admin_user.tenant_id)
    return query.all()

@router.put("/{shop_id}", response_model=ShopResponse)
@router.patch("/{shop_id}", response_model=ShopResponse)
async def update_shop(
    shop_id: UUID,
    request: ShopUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: Update an existing outlet across all 5 sections.
    """
    outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == shop_id).first()
    shop = db.query(Shop).filter(Shop.id == shop_id).first()

    if not outlet and not shop:
        raise HTTPException(status_code=404, detail="Outlet/Shop not found")

    extra = request.extra_data or (outlet.service_settings.get("extra_data") if outlet and outlet.service_settings else {})

    if outlet:
        if request.name: outlet.name = request.name
        if request.code: outlet.code = request.code
        if request.status is not None: outlet.is_active = (request.status != "Inactive")
        
        # Merge model_extra if present
        if hasattr(request, "model_extra") and request.model_extra:
            extra.update(request.model_extra)

        if "address_line1" in extra or request.address:
            addr_val = extra.get("address_line1") or request.address or ""
            if extra.get("address_line2"):
                addr_val = f"{addr_val}, {extra.get('address_line2')}".strip(", ")
            outlet.address = addr_val
        if "city" in extra or request.city:
            outlet.city = extra.get("city") or request.city
        if "state" in extra: outlet.state = extra["state"]
        if "pin_code" in extra: outlet.pin_code = extra["pin_code"]
        if "country" in extra: outlet.country = extra["country"]
        if "contact_number" in extra or request.contact_number:
            outlet.phone = extra.get("contact_number") or request.contact_number
        if "email" in extra: outlet.email = extra["email"]
        if "outlet_type" in extra: outlet.outlet_type = extra["outlet_type"]
        if "gstin" in extra: outlet.gstin = extra["gstin"]
        if "fssai" in extra: outlet.fssai = extra["fssai"]
        if "invoice_prefix" in extra: outlet.invoice_prefix = extra["invoice_prefix"]
        if "tax_rate" in extra:
            try: outlet.tax_rate = float(extra["tax_rate"])
            except (ValueError, TypeError): pass
        if "opening_time" in extra: outlet.opening_time = extra["opening_time"]
        if "closing_time" in extra: outlet.closing_time = extra["closing_time"]
        if "weekly_closing" in extra: outlet.weekly_closing = extra["weekly_closing"]
        if "description" in extra: outlet.description = extra["description"]
        if "logo_url" in extra: outlet.logo_url = extra["logo_url"]
        if "time_zone" in extra: outlet.timezone = extra["time_zone"]
        if "currency" in extra: outlet.currency = extra["currency"]
        if "upi_id" in extra: outlet.upi_id = extra["upi_id"]
        if "bank_name" in extra: outlet.bank_name = extra["bank_name"]
        if "bank_account_no" in extra: outlet.bank_account_no = extra["bank_account_no"]
        elif "ac_number" in extra: outlet.bank_account_no = extra["ac_number"]
        if "bank_ifsc" in extra: outlet.bank_ifsc = extra["bank_ifsc"]
        elif "ifsc_code" in extra: outlet.bank_ifsc = extra["ifsc_code"]
        if "bank_branch" in extra: outlet.bank_branch = extra["bank_branch"]
        elif "branch_name" in extra: outlet.bank_branch = extra["branch_name"]
        if "bank_account_name" in extra: outlet.bank_account_name = extra["bank_account_name"]
        elif "ac_holder_name" in extra: outlet.bank_account_name = extra["ac_holder_name"]
        elif "account_holder_name" in extra: outlet.bank_account_name = extra["account_holder_name"]
        elif request.account_holder_name: outlet.bank_account_name = request.account_holder_name

        svc = dict(outlet.service_settings or {})
        if request.contact_number: svc["phone"] = request.contact_number
        if request.address: svc["address"] = request.address
        if request.city: svc["city"] = request.city
        if "is_primary" in extra: svc["is_primary"] = bool(extra["is_primary"])
        elif request.is_primary is not None: svc["is_primary"] = bool(request.is_primary)
        if "enable_dine_in" in extra: svc["dine_in_enabled"] = bool(extra["enable_dine_in"])
        if "enable_takeaway" in extra: svc["takeaway_enabled"] = bool(extra["enable_takeaway"])
        if "enable_delivery" in extra: svc["delivery_enabled"] = bool(extra["enable_delivery"])
        if extra:
            svc["extra_data"] = extra
            for k in ["phone", "address", "city", "state", "pin_code", "country", "email", "outlet_type", "gstin", "fssai", "invoice_prefix", "tax_rate", "opening_time", "closing_time", "weekly_closing", "description", "logo_url", "upi_id", "bank_name", "bank_account_no", "bank_ifsc", "bank_branch", "bank_account_name", "account_holder_name", "ac_number", "ifsc_code", "branch_name", "ac_holder_name"]:
                if k in extra:
                    svc[k] = extra[k]
            if "gstin" in extra: svc["gst_number"] = extra["gstin"]
            if "upi_id" in extra: svc["upi_id"] = extra["upi_id"]

            # Update module login credentials in User table
            mod_accs = extra.get("module_accounts") or {}
            for mod_key, creds in mod_accs.items():
                uname = creds.get("username")
                upass = creds.get("password")
                urole = creds.get("role", "CASHIER")
                if uname:
                    u_record = db.query(User).filter(User.email == uname).first()
                    if u_record:
                        if upass: u_record.password = upass
                        u_record.role = urole
                        u_record.outlet_id = outlet.id
                    else:
                        new_u = User(
                            tenant_id=outlet.tenant_id,
                            outlet_id=outlet.id,
                            email=uname,
                            name=creds.get("name", f"{outlet.name} {mod_key.upper()}"),
                            phone=svc.get("phone", "9999999999"),
                            role=urole,
                            password=upass or "password123",
                            is_active=True
                        )
                        db.add(new_u)
            svc["module_accounts"] = mod_accs

        outlet.service_settings = svc

    if shop:
        update_data = request.model_dump(exclude_unset=True, exclude={"extra_data"})
        for key, value in update_data.items():
            setattr(shop, key, value)

    db.commit()

    # Formulate updated response
    target_id = (outlet.id if outlet else shop.id)
    name = (outlet.name if outlet else shop.name)
    code = (outlet.code if outlet else shop.code)
    addr = ((outlet.service_settings or {}).get("address") if outlet else shop.address)
    city = ((outlet.service_settings or {}).get("city") if outlet else shop.city)
    phone = ((outlet.service_settings or {}).get("phone") if outlet else shop.contact_number)
    stat = ("Active" if (outlet.is_active if outlet else shop.status == "Active") else "Inactive")
    prim = ((outlet.service_settings or {}).get("is_primary", False) if outlet else shop.is_primary)
    created = (outlet.created_at if outlet else shop.created_at)
    acc_holder = (outlet.bank_account_name if outlet else getattr(shop, "account_holder_name", None)) or extra.get("bank_account_name") or extra.get("ac_holder_name") or extra.get("account_holder_name")

    return ShopResponse(
        id=target_id,
        tenant_id=admin_user.tenant_id,
        name=name,
        code=code,
        address=addr or "",
        city=city or "",
        contact_number=phone or "",
        status=stat,
        is_primary=prim,
        account_holder_name=acc_holder,
        created_at=created,
        extra_data=extra
    )

from models.restaurant_menu import RestaurantMenuCategory, RestaurantMenuItem
from models.restaurant_table import RestaurantTable
from models.restaurant_order import RestaurantOrder
from models.restaurant_shift import RestaurantShift
from models.restaurant_customer import RestaurantCustomer
from models.restaurant_ingredient import RestaurantIngredient
from models.restaurant_stock_ledger import RestaurantStockLedger
from models.restaurant_modifier import RestaurantModifierGroup
from models.restaurant_audit import RestaurantAuditEvent
from models.shop_settings import ShopSettings

def cascade_delete_outlet_and_data(outlet_id: UUID, db: Session):
    """
    Completely purges all data associated with an outlet:
    1. Removes all module user credentials (e.g. {code}_pos, {code}_kds, {code}_inv, {code}_crm, etc.)
    2. Deletes all menu items, categories, modifier groups
    3. Deletes all tables, orders, kitchen tickets, shifts, stock ledger, ingredients, audit events
    4. Deletes shop settings, inventory items, shop bills, and legacy shop record
    5. Deletes the RestaurantOutlet record
    """
    outlet = db.query(RestaurantOutlet).filter(RestaurantOutlet.id == outlet_id).first()
    shop = db.query(Shop).filter(Shop.id == outlet_id).first()
    
    # Identify usernames/emails associated with this outlet
    target_emails = set()
    outlet_code = None
    if outlet:
        outlet_code = (outlet.code or "").lower().replace("-", "").replace(" ", "")
        svc = outlet.service_settings or {}
        mod_accounts = svc.get("module_accounts") or {}
        for cred in mod_accounts.values():
            if isinstance(cred, dict) and cred.get("username"):
                target_emails.add(cred["username"].strip().lower())
    if shop and not outlet_code:
        outlet_code = (shop.code or "").lower().replace("-", "").replace(" ", "")

    if outlet_code:
        # Also clean up standard station patterns: {code}_pos, {code}_kds, {code}_inv, {code}_crm
        for suffix in ["_pos", "_kds", "_inv", "_crm", "_mgr"]:
            target_emails.add(f"{outlet_code}{suffix}")
        for prefix in ["pos_", "kitchen_", "inventory_", "crm_"]:
            target_emails.add(f"{prefix}{outlet_code}@sirfbill.com")

    # 1. Delete associated module user accounts
    if target_emails:
        db.query(User).filter(
            or_(*[User.email.ilike(em) for em in target_emails])
        ).delete(synchronize_session=False)

    # 2. Delete inventory items and bills explicitly linked to this shop/outlet
    db.query(InventoryItem).filter(InventoryItem.shop_id == outlet_id).delete(synchronize_session=False)
    db.query(ShopSettings).filter(ShopSettings.shop_id == outlet_id).delete(synchronize_session=False)

    # 3. Clean up restaurant orders, tables, menus, etc.
    # Note: Foreign key constraints on restaurant_outlets have ON DELETE CASCADE,
    # but explicit deletion ensures total cleanup across both standalone & foreign-key tables
    db.query(RestaurantOrder).filter(RestaurantOrder.outlet_id == outlet_id).delete(synchronize_session=False)
    db.query(RestaurantTable).filter(RestaurantTable.outlet_id == outlet_id).delete(synchronize_session=False)
    db.query(RestaurantMenuItem).filter(RestaurantMenuItem.outlet_id == outlet_id).delete(synchronize_session=False)
    db.query(RestaurantMenuCategory).filter(RestaurantMenuCategory.outlet_id == outlet_id).delete(synchronize_session=False)
    db.query(RestaurantModifierGroup).filter(RestaurantModifierGroup.outlet_id == outlet_id).delete(synchronize_session=False)
    db.query(RestaurantShift).filter(RestaurantShift.outlet_id == outlet_id).delete(synchronize_session=False)
    db.query(RestaurantIngredient).filter(RestaurantIngredient.outlet_id == outlet_id).delete(synchronize_session=False)
    db.query(RestaurantStockLedger).filter(RestaurantStockLedger.outlet_id == outlet_id).delete(synchronize_session=False)
    db.query(RestaurantCustomer).filter(RestaurantCustomer.outlet_id == outlet_id).delete(synchronize_session=False)
    db.query(RestaurantAuditEvent).filter(RestaurantAuditEvent.outlet_id == outlet_id).delete(synchronize_session=False)

    # 4. Delete the primary records
    if outlet:
        db.delete(outlet)
    if shop:
        db.delete(shop)

@router.delete("/{shop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shop(
    shop_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin Action: Delete an outlet/shop and cascade delete all its credentials,
    menus, categories, tables, orders, inventory, and configuration.
    """
    cascade_delete_outlet_and_data(shop_id, db)
    db.commit()
    return None


@router.get("/inventory")
async def get_inventory(
    shop_id: UUID,
    search: str = None,
    start_date: str = None,
    end_date: str = None,
    category_id: UUID = None,
    distributor_id: UUID = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Admin Action: Fetches the inventory for a given shop.
    """
    query = (
        db.query(InventoryItem)
        .outerjoin(Category, InventoryItem.category_id == Category.id)
        .outerjoin(Rack, InventoryItem.rack_id == Rack.id)
        .outerjoin(Distributor, InventoryItem.distributor_id == Distributor.id)
        .filter(InventoryItem.shop_id == shop_id, InventoryItem.is_deleted == 0)
    )
    
    if search and search.strip():
        search_terms = [s.strip() for s in search.strip().split() if s.strip()]
        for term in search_terms:
            pattern = f"%{term}%"
            query = query.filter(
                or_(
                    InventoryItem.name.ilike(pattern),
                    InventoryItem.sku.ilike(pattern),
                    InventoryItem.manufacturer.ilike(pattern),
                    InventoryItem.batch_number.ilike(pattern),
                    InventoryItem.hsn_code.ilike(pattern),
                    InventoryItem.distributor.ilike(pattern),
                    Distributor.name.ilike(pattern),
                    Category.name.ilike(pattern),
                    Category.description.ilike(pattern),
                    Rack.rack_number.ilike(pattern),
                    Rack.details.ilike(pattern),
                    cast(InventoryItem.expiry_date, String).ilike(pattern),
                    cast(InventoryItem.unit_price, String).ilike(pattern),
                    cast(InventoryItem.buying_price, String).ilike(pattern),
                )
            )
        
    if start_date:
        query = query.filter(InventoryItem.created_at >= start_date)
        
    if end_date:
        # Add 23:59:59 to end_date if it's just YYYY-MM-DD
        end_date_str = end_date if "T" in end_date else f"{end_date}T23:59:59"
        query = query.filter(InventoryItem.created_at <= end_date_str)
        
    if category_id:
        query = query.filter(InventoryItem.category_id == category_id)
        
    if distributor_id:
        query = query.filter(InventoryItem.distributor_id == distributor_id)
        
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    for item in items:
        if (not item.distributor or item.distributor.strip() == "") and item.distributor_rel:
            item.distributor = item.distributor_rel.name
    
    return {
        "total": total,
        "items": items
    }

@router.post("/upload-inventory", status_code=status.HTTP_201_CREATED)
async def upload_inventory_excel(
    shop_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # 🛡️ SECURED
):
    """
    Admin Action: Uploads massive .xlsx files for pharmacy inventory.
    """
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Only Excel and CSV files are supported for bulk inventory.")

    try:
        if file.filename.endswith('.csv'):
            import csv
            file.file.seek(0)
            decoded_file = (line.decode('utf-8') for line in file.file)
            reader = csv.reader(decoded_file)
            rows = list(reader)
        else:
            # Load the spooled file into calamine (memory-safe)
            workbook = python_calamine.CalamineWorkbook.from_filelike(file.file)
            sheet_name = workbook.sheet_names[0]
            rows = workbook.get_sheet_by_name(sheet_name).to_python(skip_empty_area=True)

        header_row = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []
        
        col_map = {}
        for idx, col in enumerate(header_row):
            raw_col = str(col).strip().lower()
            clean_col = "".join(c if c.isalnum() else "_" for c in raw_col)
            while "__" in clean_col:
                clean_col = clean_col.replace("__", "_")
            clean_col = clean_col.strip("_")

            if clean_col in ["stock_quantity", "stock", "qty", "quantity"]: col_name = "quantity"
            elif clean_col in ["loose_stock", "loose_qty"]: col_name = "loose_stock"
            elif clean_col in ["pack_size", "pack"]: col_name = "pack_size"
            elif clean_col in ["unit_price", "mrp", "selling_price", "rate", "price"]: col_name = "price"
            elif clean_col in ["buying_price", "purchase_price", "cost_price", "cost"]: col_name = "buying_price"
            elif clean_col in ["batch_number", "batch_no", "batch"]: col_name = "batch"
            elif clean_col in ["expiry_date", "exp_date", "expiry"]: col_name = "expiry"
            elif clean_col in ["hsn_code", "hsn"]: col_name = "hsn_code"
            elif clean_col in ["gst", "tax", "gst_rate"]: col_name = "gst"
            elif clean_col in ["discount", "disc"]: col_name = "discount"
            elif clean_col in ["manufacturer", "brand", "company", "make"]: col_name = "manufacturer"
            elif clean_col in ["item_name", "product_name", "name"]: col_name = "name"
            elif clean_col in ["sku", "barcode", "code", "item_code"]: col_name = "sku"
            elif clean_col in ["rack", "rack_no", "rack_number", "shelf"]: col_name = "rack"
            elif clean_col in ["category", "cat", "group"]: col_name = "category"
            elif clean_col in ["distributor", "supplier", "vendor"]: col_name = "distributor"
            else: col_name = clean_col
            col_map[col_name] = idx
            
        if "name" not in col_map:
            col_map = {"name": 0, "sku": 1, "batch": 2, "quantity": 3, "price": 4, "expiry": 5}
        
        items_added = 0
        batch_size = 1000 # Process in manageable batches
        
        from datetime import datetime
        
        existing_records = db.query(InventoryItem.name, InventoryItem.sku).filter(
            InventoryItem.shop_id == shop_id
        ).all()
        
        existing_names = {r.name for r in existing_records if r.name}
        existing_skus = {r.sku for r in existing_records if r.sku and str(r.sku).strip() not in ["", "-"]}
        
        categories_map = {
            c.name.strip().lower(): c.id 
            for c in db.query(Category).filter(Category.shop_id == shop_id).all() 
            if c.name
        }
        racks_map = {
            r.rack_number.strip().lower(): r.id 
            for r in db.query(Rack).filter(Rack.shop_id == shop_id).all() 
            if r.rack_number
        }
        distributors_map = {
            d.name.strip().lower(): d.id 
            for d in db.query(Distributor).filter(
                (Distributor.shop_id == shop_id) | (Distributor.tenant_id == admin_user.tenant_id)
            ).all() 
            if d.name
        }

        for row in data_rows:
            def get_val(key, default=""):
                idx = col_map.get(key, -1)
                if 0 <= idx < len(row):
                    return row[idx]
                return default

            name_val = str(get_val("name", "")).strip() or 'Unknown'
            sku_val = str(get_val("sku", "")).strip() or 'Unknown'
            
            if name_val in existing_names: continue
            if sku_val not in ["", "-", "Unknown"] and sku_val in existing_skus: continue
                
            existing_names.add(name_val)
            if sku_val not in ["", "-", "Unknown"]: existing_skus.add(sku_val)
            
            try:
                stock_qty = int(float(str(get_val("quantity", 0)).strip() or 0))
            except (ValueError, TypeError):
                stock_qty = 0

            try:
                unit_price = float(str(get_val("price", 0.0)).strip() or 0.0)
            except (ValueError, TypeError):
                unit_price = 0.0

            exp = get_val("expiry", "")
            if isinstance(exp, str) and exp:
                try:
                    exp = datetime.strptime(exp.strip(), "%Y-%m-%d").date()
                except ValueError:
                    exp = datetime.utcnow().date()
            elif hasattr(exp, 'date'):
                exp = exp.date()
            elif hasattr(exp, 'to_pydatetime'):
                exp = exp.to_pydatetime().date()
            else:
                exp = datetime.utcnow().date()

            try:
                buying_price = float(str(get_val("buying_price", 0.0)).strip() or 0.0)
            except (ValueError, TypeError):
                buying_price = 0.0
                
            try:
                gst_val = float(str(get_val("gst", 0.0)).strip() or 0.0)
            except (ValueError, TypeError):
                gst_val = 0.0

            try:
                loose_stock = int(float(str(get_val("loose_stock", 0)).strip() or 0))
            except (ValueError, TypeError):
                loose_stock = 0

            try:
                pack_size = int(float(str(get_val("pack_size", 1)).strip() or 1))
            except (ValueError, TypeError):
                pack_size = 1

            try:
                discount_val = float(str(get_val("discount", 0.0)).strip() or 0.0)
            except (ValueError, TypeError):
                discount_val = 0.0

            # Category auto-create / lookup
            cat_name_raw = str(get_val("category", "")).strip()
            cat_id = None
            if cat_name_raw and cat_name_raw.lower() not in ["", "none", "null", "-", "n/a"]:
                cat_key = cat_name_raw.lower()
                if cat_key in categories_map:
                    cat_id = categories_map[cat_key]
                else:
                    new_cat = Category(
                        shop_id=shop_id,
                        name=cat_name_raw,
                        is_active=True
                    )
                    db.add(new_cat)
                    db.flush()
                    categories_map[cat_key] = new_cat.id
                    cat_id = new_cat.id

            # Distributor auto-create / lookup
            dist_name_raw = str(get_val("distributor", "")).strip()
            dist_id = None
            distributor_val = None
            if dist_name_raw and dist_name_raw.lower() not in ["", "none", "null", "-", "n/a"]:
                distributor_val = dist_name_raw
                dist_key = dist_name_raw.lower()
                if dist_key in distributors_map:
                    dist_id = distributors_map[dist_key]
                else:
                    new_dist = Distributor(
                        tenant_id=admin_user.tenant_id,
                        shop_id=shop_id,
                        name=dist_name_raw,
                        is_active=True
                    )
                    db.add(new_dist)
                    db.flush()
                    distributors_map[dist_key] = new_dist.id
                    dist_id = new_dist.id

            # Rack auto-create / lookup
            rack_no_raw = str(get_val("rack", "")).strip()
            rack_id = None
            if rack_no_raw and rack_no_raw.lower() not in ["", "none", "null", "-", "n/a"]:
                rack_key = rack_no_raw.lower()
                if rack_key in racks_map:
                    rack_id = racks_map[rack_key]
                else:
                    new_rack = Rack(
                        shop_id=shop_id,
                        rack_number=rack_no_raw,
                        is_active=True
                    )
                    db.add(new_rack)
                    db.flush()
                    racks_map[rack_key] = new_rack.id
                    rack_id = new_rack.id

            new_item = InventoryItem(
                tenant_id=admin_user.tenant_id,
                shop_id=shop_id,
                name=name_val,
                sku=sku_val,
                manufacturer=str(get_val("manufacturer", "")).strip() or 'Unknown',
                batch_number=str(get_val("batch", "")).strip() or 'N/A',
                hsn_code=str(get_val("hsn_code", "")).strip() or 'None',
                stock_quantity=stock_qty,
                loose_stock=loose_stock,
                pack_size=pack_size,
                buying_price=buying_price,
                unit_price=unit_price,
                expiry_date=exp,
                gst=gst_val,
                discount=discount_val,
                distributor=distributor_val,
                distributor_id=dist_id,
                category_id=cat_id,
                rack_id=rack_id
            )
            db.add(new_item)
            items_added += 1
            
            # Commit chunks to keep memory profile completely flat[cite: 1]
            if items_added % batch_size == 0:
                db.commit()
                
        db.commit() # Final commit
        return {"message": f"Successfully parsed and uploaded {items_added} inventory items."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process Excel file: {str(e)}")
    finally:
        file.file.close()

@router.post("/inventory/add", status_code=status.HTTP_201_CREATED)
def add_inventory_item(
    item_in: InventoryItemCreate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    # 1. Check if it already exists in the same shop (by SKU only, allowing same names for different batches/brands)
    from sqlalchemy import or_, and_
    conditions = []
    # Only check for duplicate SKU if the SKU actually contains a value (ignoring common defaults like '-' or empty)
    if item_in.sku and item_in.sku.strip() not in ["", "-"]:
        conditions.append(InventoryItem.sku == item_in.sku)
        
    if conditions:
        existing_item = db.query(InventoryItem).filter(
            InventoryItem.shop_id == item_in.shop_id,
            or_(*conditions)
        ).first()
        
        if existing_item:
            raise HTTPException(status_code=400, detail="Medicine with this SKU already exists in this shop.")

    # 2. Create the SQLAlchemy model instance
    item_data = item_in.model_dump()
    item_data["tenant_id"] = admin_user.tenant_id
    new_item = InventoryItem(**item_data)
    
    # Auto-sync distributor name and distributor_id
    if new_item.distributor_id and (not new_item.distributor or new_item.distributor.strip() == ""):
        dist = db.query(Distributor).filter(Distributor.id == new_item.distributor_id).first()
        if dist:
            new_item.distributor = dist.name
    elif new_item.distributor and not new_item.distributor_id:
        dist = db.query(Distributor).filter(
            Distributor.shop_id == new_item.shop_id,
            Distributor.name.ilike(new_item.distributor.strip())
        ).first()
        if dist:
            new_item.distributor_id = dist.id

    # 3. Save to database
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return {"status": "success", "message": "Medicine added", "data": new_item}

@router.patch("/inventory/{item_id}/update")
def update_inventory_item(
    item_id: UUID, 
    item_in: InventoryItemUpdate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    # 1. Find the item
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Medicine not found.")

    if admin_user.tenant_id and item.tenant_id != admin_user.tenant_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # 2. Extract only the fields the Flutter app actually sent
    update_data = item_in.model_dump(exclude_unset=True)
    
    # 3. Apply the changes
    for key, value in update_data.items():
        setattr(item, key, value)
        
    # Auto-sync distributor name and distributor_id
    if item.distributor_id and (not item.distributor or item.distributor.strip() == ""):
        dist = db.query(Distributor).filter(Distributor.id == item.distributor_id).first()
        if dist:
            item.distributor = dist.name
    elif item.distributor and not item.distributor_id:
        dist = db.query(Distributor).filter(
            Distributor.shop_id == item.shop_id,
            Distributor.name.ilike(item.distributor.strip())
        ).first()
        if dist:
            item.distributor_id = dist.id

    db.commit()
    db.refresh(item)
    
    return {"status": "success", "message": "Medicine updated", "data": item}

@router.delete("/inventory/{item_id}/delete")
def delete_inventory_item(
    item_id: UUID, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    # 1. Find the item
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Medicine not found.")

    if admin_user.tenant_id and item.tenant_id != admin_user.tenant_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # 2. Delete it
    try:
        item.is_deleted = 1
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete this medicine because it is already linked to past bills. Please set stock to 0 instead."
        )
    
    return {"status": "success", "message": f"Medicine {item_id} successfully deleted."}

import os
import shutil
from fastapi import UploadFile, File

from dependencies import get_admin_user, get_optional_restaurant_staff

@router.post("/inventory/upload-image")
async def upload_medicine_image(
    file: UploadFile = File(...),
    admin_user: Optional[User] = Depends(get_optional_restaurant_staff)
):
    """
    Upload an image for a medicine.
    """
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png", "gif", "webp"]:
        raise HTTPException(status_code=400, detail="File must be an image (jpg, png, gif, webp).")

    # Create directory if it doesn't exist
    os.makedirs("uploads/inventory", exist_ok=True)
    
    import uuid
    file_extension = file.filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"uploads/inventory/{new_filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"image_url": f"/{file_path}"}


# --- RACK ENDPOINTS ---

@router.post("/racks", response_model=RackSchema, status_code=status.HTTP_201_CREATED)
def create_rack(
    request: RackCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    new_rack = Rack(
        shop_id=request.shop_id,
        rack_number=request.rack_number,
        details=request.details,
        is_active=request.is_active
    )
    db.add(new_rack)
    db.commit()
    db.refresh(new_rack)
    return new_rack

@router.get("/racks/", response_model=List[RackSchema])
@router.get("/racks", response_model=List[RackSchema])
def get_racks(
    shop_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    query = db.query(Rack)
    if shop_id:
        query = query.filter(Rack.shop_id == shop_id)
        
    return query.all()

@router.patch("/racks/{rack_id}/", response_model=RackSchema)
@router.patch("/racks/{rack_id}", response_model=RackSchema)
def update_rack(
    rack_id: UUID,
    request: RackUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack not found")
        
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rack, key, value)
        
    db.commit()
    db.refresh(rack)
    return rack

@router.delete("/racks/{rack_id}/")
@router.delete("/racks/{rack_id}")
def delete_rack(
    rack_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack not found")
        
    db.delete(rack)
    db.commit()
    return {"status": "success", "message": "Rack deleted successfully"}


# --- CATEGORY ENDPOINTS ---

@router.post("/categories/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
@router.post("/categories", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
def create_category(
    request: CategoryCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    new_category = Category(
        shop_id=request.shop_id,
        name=request.name,
        description=request.description,
        is_active=request.is_active
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/categories/", response_model=List[CategorySchema])
@router.get("/categories", response_model=List[CategorySchema])
def get_categories(
    shop_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    query = db.query(Category)
    if shop_id:
        query = query.filter(Category.shop_id == shop_id)
        
    return query.all()

@router.patch("/categories/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: UUID,
    request: CategoryUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
        
    db.commit()
    db.refresh(category)
    return category

@router.delete("/categories/{category_id}")
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    db.delete(category)
    db.commit()
    return {"status": "success", "message": "Category deleted successfully"}


# --- BACKWARDS COMPATIBILITY ALIAS ROUTER ---
# The frontend currently calls /api/admin/categories instead of /api/admin/shop/categories
# We'll create a secondary router without the /shop prefix just for these.

alias_router = APIRouter(
    prefix="/api/admin",
    tags=["Admin - Backwards Compatibility"]
)

# Re-route Racks
@alias_router.post("/racks/", response_model=RackSchema, status_code=status.HTTP_201_CREATED)
@alias_router.post("/racks", response_model=RackSchema, status_code=status.HTTP_201_CREATED)
def alias_create_rack(request: RackCreate, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    return create_rack(request, db, admin_user)

@alias_router.get("/racks/", response_model=List[RackSchema])
@alias_router.get("/racks", response_model=List[RackSchema])
def alias_get_racks(shop_id: Optional[UUID] = None, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    return get_racks(shop_id, db, admin_user)

@alias_router.get("/racks/{shop_id}/", response_model=List[RackSchema])
@alias_router.get("/racks/{shop_id}", response_model=List[RackSchema])
def alias_get_racks_by_path(shop_id: UUID, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    return get_racks(shop_id, db, admin_user)

@alias_router.patch("/racks/{rack_id}/", response_model=RackSchema)
@alias_router.patch("/racks/{rack_id}", response_model=RackSchema)
def alias_update_rack(rack_id: UUID, request: RackUpdate, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    return update_rack(rack_id, request, db, admin_user)

@alias_router.delete("/racks/{rack_id}/")
@alias_router.delete("/racks/{rack_id}")
def alias_delete_rack(rack_id: UUID, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    return delete_rack(rack_id, db, admin_user)


# Re-route Categories
@alias_router.post("/categories/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
@alias_router.post("/categories", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
def alias_create_category(request: CategoryCreate, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    return create_category(request, db, admin_user)

@alias_router.get("/categories/", response_model=List[CategorySchema])
@alias_router.get("/categories", response_model=List[CategorySchema])
def alias_get_categories(shop_id: Optional[UUID] = None, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    return get_categories(shop_id, db, admin_user)

@alias_router.get("/categories/{shop_id}/", response_model=List[CategorySchema])
@alias_router.get("/categories/{shop_id}", response_model=List[CategorySchema])
def alias_get_categories_by_path(shop_id: UUID, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    return get_categories(shop_id, db, admin_user)

@alias_router.patch("/categories/{category_id}/", response_model=CategorySchema)
@alias_router.patch("/categories/{category_id}", response_model=CategorySchema)
def alias_update_category(category_id: UUID, request: CategoryUpdate, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    return update_category(category_id, request, db, admin_user)

@alias_router.delete("/categories/{category_id}/")
@alias_router.delete("/categories/{category_id}")
def alias_delete_category(category_id: UUID, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    return delete_category(category_id, db, admin_user)
