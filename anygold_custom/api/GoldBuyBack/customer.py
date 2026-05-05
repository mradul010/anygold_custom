import frappe
from frappe import _
from frappe.utils import cstr
import json


# ── ACTUAL FIXTURE FIELD NAMES ───────────────────────────────────────────────
# Customer / Supplier custom fields as defined in fixtures/custom_field.json:
#   customer_nationality   — nationality (Select)
#   malaysian_id           — Malaysian IC / NRIC
#   other_id_type          — Country / nationality for foreigners
#   other_id_number        — Passport / ID number for foreigners
#   bank_name              — Bank name
#   bank_account_number    — Bank account number


def _has(doctype, field):
    return frappe.db.has_column(doctype, field)


# ── SEARCH ───────────────────────────────────────────────────────────────────

@frappe.whitelist()
def search_goldbuyback_customers(query="", limit=20):
    """
    Search customers by name, IC, passport, or mobile.
    Returns fields needed by the Gold Buyback UI.
    """
    q     = cstr(query).strip()
    limit = min(int(limit or 20), 100)

    base_fields = ["name", "customer_name", "mobile_no", "customer_group"]
    extra_fields = [
        "customer_nationality", "malaysian_id", "other_id_type",
        "other_id_number", "bank_name", "bank_account_number",
    ]
    fields = base_fields + [f for f in extra_fields if _has("Customer", f)]

    if not q:
        return frappe.get_all(
            "Customer",
            fields=fields,
            order_by="modified desc",
            limit_page_length=limit,
        )

    or_filters = [["customer_name", "like", f"%{q}%"]]
    for cf in ["malaysian_id", "other_id_number"]:
        if _has("Customer", cf):
            or_filters.append([cf, "like", f"%{q}%"])
    or_filters.append(["mobile_no", "like", f"%{q}%"])

    return frappe.get_all(
        "Customer",
        fields=fields,
        or_filters=or_filters,
        order_by="modified desc",
        limit_page_length=limit,
    )


# ── CREATE ────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_goldbuyback_customer(data):
    """
    Create a Customer + linked Supplier for the Gold Buyback module.

    Input keys: customer_name, nationality, customer_type, mobile_no,
                ic_number, passport_number, country,
                bank_name, bank_account_number, customer_photo

    Returns:
      { success, duplicate, message, customer: {...}, supplier: {...} }
    """
    data = json.loads(data) if isinstance(data, str) else data

    customer_name       = cstr(data.get("customer_name", "")).strip().upper()
    nationality         = cstr(data.get("nationality", "")).strip()
    customer_type       = cstr(data.get("customer_type", "Individual")).strip()
    mobile_no           = cstr(data.get("mobile_no", "")).strip()
    # Malaysian IC stored in 'malaysian_id'; non-Malaysian ID in 'other_id_number'
    malaysian_id        = cstr(data.get("malaysian_id", "")).strip()
    other_id_number     = cstr(data.get("other_id_number", "")).strip()
    other_id_type       = cstr(data.get("other_id_type", "")).strip()
    bank_name           = cstr(data.get("bank_name", "")).strip()
    bank_account_number = cstr(data.get("bank_account_number", "")).strip()

    # ── Validate ──────────────────────────────────────────────────────────────
    if not customer_name:
        frappe.throw(_("Customer Name is required."))
    if not nationality:
        frappe.throw(_("Nationality is required."))
    if not customer_type:
        frappe.throw(_("Customer Type is required."))
    if not mobile_no:
        frappe.throw(_("Mobile Number is required."))

    is_malaysian = (nationality == "Malaysian")
    if is_malaysian:
        if not malaysian_id:
            frappe.throw(_("IC Number (malaysian_id) is required for Malaysian customers."))
    else:
        if not other_id_number:
            frappe.throw(_("Passport / ID Number is required for non-Malaysian customers."))
        if not other_id_type:
            frappe.throw(_("Country / ID Type is required for non-Malaysian customers."))

    # ── Duplicate check ───────────────────────────────────────────────────────
    if is_malaysian and _has("Customer", "malaysian_id"):
        existing = frappe.db.get_value(
            "Customer", {"malaysian_id": malaysian_id}, ["name", "customer_name"], as_dict=True
        )
        if existing:
            cust_doc = frappe.get_doc("Customer", existing.name)
            return {
                "success": True, "duplicate": True,
                "message": _("Customer already exists. Selected existing customer."),
                "customer": _customer_response(cust_doc),
                "supplier": _find_linked_supplier(cust_doc.name, malaysian_id, ""),
            }

    if not is_malaysian and _has("Customer", "other_id_number"):
        existing = frappe.db.get_value(
            "Customer", {"other_id_number": other_id_number}, ["name", "customer_name"], as_dict=True
        )
        if existing:
            cust_doc = frappe.get_doc("Customer", existing.name)
            return {
                "success": True, "duplicate": True,
                "message": _("Customer already exists. Selected existing customer."),
                "customer": _customer_response(cust_doc),
                "supplier": _find_linked_supplier(cust_doc.name, "", other_id_number),
            }

    # ── Create Customer ───────────────────────────────────────────────────────
    group = _resolve_customer_group(customer_type)
    territory = (
        frappe.db.get_single_value("Selling Settings", "territory")
        or frappe.db.get_value("Territory", {"is_group": 0}, "name")
        or "All Territories"
    )

    cust_fields = {
        "doctype":        "Customer",
        "customer_name":  customer_name,
        "customer_group": group,
        "territory":      territory,
        "mobile_no":      mobile_no,
    }
    _set_if_exists(cust_fields, "Customer", "customer_nationality", nationality)
    if is_malaysian:
        _set_if_exists(cust_fields, "Customer", "malaysian_id",     malaysian_id)
        _set_if_exists(cust_fields, "Customer", "other_id_number",  "")
        _set_if_exists(cust_fields, "Customer", "other_id_type",    "")
    else:
        _set_if_exists(cust_fields, "Customer", "malaysian_id",     "")
        _set_if_exists(cust_fields, "Customer", "other_id_number",  other_id_number)
        _set_if_exists(cust_fields, "Customer", "other_id_type",    other_id_type)
    _set_if_exists(cust_fields, "Customer", "bank_name",            bank_name)
    _set_if_exists(cust_fields, "Customer", "bank_account_number",  bank_account_number)

    cust_doc = frappe.get_doc(cust_fields)
    cust_doc.insert(ignore_permissions=True)

    # ── Create linked Supplier ────────────────────────────────────────────────
    supplier = _create_or_update_supplier(
        customer_name=customer_name,
        nationality=nationality,
        malaysian_id=malaysian_id,
        other_id_number=other_id_number,
        other_id_type=other_id_type,
        bank_name=bank_name,
        bank_account_number=bank_account_number,
        is_malaysian=is_malaysian,
    )

    frappe.db.commit()

    return {
        "success":   True,
        "duplicate": False,
        "customer":  _customer_response(cust_doc),
        "supplier":  supplier,
    }


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _set_if_exists(target_dict, doctype, field, value):
    """Only add a field to the dict if the column exists in the DB."""
    if _has(doctype, field):
        target_dict[field] = value


def _customer_response(cust_doc):
    def gv(f): return getattr(cust_doc, f, None) or ""
    return {
        "name":                 cust_doc.name,
        "customer_name":        cust_doc.customer_name or "",
        "mobile_no":            cust_doc.mobile_no or "",
        "customer_group":       cust_doc.customer_group or "",
        "nationality":          gv("customer_nationality"),
        "ic_number":            gv("malaysian_id"),
        "passport_number":      gv("other_id_number"),
        "country":              gv("other_id_type"),
        "bank_name":            gv("bank_name"),
        "bank_account_number":  gv("bank_account_number"),
    }


def _find_linked_supplier(customer_doc_name, ic="", passport=""):
    """Try to find an existing supplier linked to this customer by IC or passport."""
    if ic and _has("Supplier", "malaysian_id"):
        row = frappe.db.get_value("Supplier", {"malaysian_id": ic}, ["name", "supplier_name"], as_dict=True)
        if row:
            return {"name": row.name, "supplier_name": row.supplier_name}
    if passport and _has("Supplier", "other_id_number"):
        row = frappe.db.get_value("Supplier", {"other_id_number": passport}, ["name", "supplier_name"], as_dict=True)
        if row:
            return {"name": row.name, "supplier_name": row.supplier_name}
    return None


def _create_or_update_supplier(
    customer_name, nationality,
    malaysian_id, other_id_number, other_id_type,
    bank_name, bank_account_number, is_malaysian,
):
    """Create or update a Supplier mirror for this Customer."""
    sup_name = None
    if is_malaysian and malaysian_id and _has("Supplier", "malaysian_id"):
        sup_name = frappe.db.get_value("Supplier", {"malaysian_id": malaysian_id}, "name")
    if not sup_name and not is_malaysian and other_id_number and _has("Supplier", "other_id_number"):
        sup_name = frappe.db.get_value("Supplier", {"other_id_number": other_id_number}, "name")
    if not sup_name:
        sup_name = frappe.db.get_value("Supplier", {"supplier_name": customer_name}, "name")

    sup_fields = {
        "supplier_name":  customer_name,
        "supplier_group": _resolve_supplier_group(),
        "supplier_type":  "Individual",
    }
    _set_if_exists(sup_fields, "Supplier", "customer_nationality", nationality)
    if is_malaysian:
        _set_if_exists(sup_fields, "Supplier", "malaysian_id",    malaysian_id)
        _set_if_exists(sup_fields, "Supplier", "other_id_number", "")
        _set_if_exists(sup_fields, "Supplier", "other_id_type",   "")
    else:
        _set_if_exists(sup_fields, "Supplier", "malaysian_id",    "")
        _set_if_exists(sup_fields, "Supplier", "other_id_number", other_id_number)
        _set_if_exists(sup_fields, "Supplier", "other_id_type",   other_id_type)
    _set_if_exists(sup_fields, "Supplier", "bank_name",            bank_name)
    _set_if_exists(sup_fields, "Supplier", "bank_account_number",  bank_account_number)

    if sup_name:
        for field, val in sup_fields.items():
            if field in ("supplier_name", "supplier_group", "supplier_type"):
                continue
            try:
                frappe.db.set_value("Supplier", sup_name, field, val, update_modified=False)
            except Exception:
                pass
        return {"name": sup_name, "supplier_name": customer_name}

    try:
        sup_doc = frappe.get_doc({"doctype": "Supplier", **sup_fields})
        sup_doc.insert(ignore_permissions=True)
        return {"name": sup_doc.name, "supplier_name": sup_doc.supplier_name}
    except frappe.DuplicateEntryError:
        frappe.db.rollback()
        existing_name = frappe.db.get_value("Supplier", {"supplier_name": customer_name}, "name")
        if existing_name:
            return {"name": existing_name, "supplier_name": customer_name}
        return None
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Gold Buyback — Supplier creation failed")
        return None


def _resolve_customer_group(customer_type):
    for preferred in (customer_type, "Individual", "Commercial", "All Customer Groups"):
        if frappe.db.exists("Customer Group", preferred):
            return preferred
    groups = frappe.get_all("Customer Group", filters={"is_group": 0}, fields=["name"], limit=1)
    return groups[0].name if groups else "Individual"


def _resolve_supplier_group():
    for preferred in ("Wholesale Gold Supplier", "Gold Supplier", "All Supplier Groups"):
        if frappe.db.exists("Supplier Group", preferred):
            return preferred
    groups = frappe.get_all("Supplier Group", filters={"is_group": 0}, fields=["name"], limit=1)
    return groups[0].name if groups else "All Supplier Groups"
