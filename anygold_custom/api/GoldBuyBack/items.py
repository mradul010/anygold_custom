import frappe
from frappe import _

# Suffixes that define the three wholesale item variants per purity
_WS_SUFFIXES = ["N", "WG", "EBTS"]


@frappe.whitelist()
def create_purity_with_items(purity_code, description="", xau_coefficient=0.0):
    """
    1. Validates the purity code (digits only, not already in Purity Master).
    2. Creates the Purity Master record.
    3. Creates three Item records: WS-{purity}-N, WS-{purity}-WG, WS-{purity}-EBTS.
    Returns { created, purity_code, items, message }.
    """
    purity_code = (purity_code or "").strip().upper()
    if not purity_code:
        frappe.throw(_("Purity code is required."))

    # Check for duplicate in Purity Master
    if frappe.db.exists("Purity Master", purity_code):
        existing = frappe.db.get_value(
            "Purity Master", purity_code, ["purity_code", "xau_coefficient", "is_active"], as_dict=True
        )
        return {
            "created": False,
            "duplicate": True,
            "purity_code": purity_code,
            "message": f"Purity {purity_code} already exists.",
            "existing": existing,
        }

    # Create Purity Master record
    pm = frappe.new_doc("Purity Master")
    pm.purity_code     = purity_code
    pm.description     = description or f"Purity {purity_code}"
    pm.xau_coefficient = float(xau_coefficient or 0)
    pm.is_active       = 1
    pm.insert(ignore_permissions=True)

    # Resolve item group and UOM (reuse helpers from submit.py)
    from anygold_custom.api.GoldBuyBack.submit import get_default_item_group, get_weight_uom
    item_group = get_default_item_group()
    stock_uom  = get_weight_uom()

    created_items = []
    for suffix in _WS_SUFFIXES:
        item_code = f"WS-{purity_code}-{suffix}"
        if frappe.db.exists("Item", item_code):
            created_items.append({"item_code": item_code, "skipped": True})
            continue

        item = frappe.new_doc("Item")
        item.item_code   = item_code
        item.item_name   = item_code
        item.item_group  = item_group
        item.stock_uom   = stock_uom
        item.description = f"Wholesale Gold {suffix} – Purity {purity_code}"
        item.is_stock_item = 1
        item.insert(ignore_permissions=True)
        created_items.append({"item_code": item_code, "skipped": False})

    frappe.db.commit()

    return {
        "created": True,
        "duplicate": False,
        "purity_code": purity_code,
        "message": f"Purity {purity_code} created with {len([i for i in created_items if not i['skipped']])} new items.",
        "items": created_items,
    }


@frappe.whitelist()
def get_purity_master():
	"""Return active purity codes with XAU coefficients from Purity Master."""
	records = frappe.get_all(
		"Purity Master",
		filters={"is_active": 1},
		fields=["purity_code", "xau_coefficient"],
		order_by="purity_code asc"
	)
	return records


@frappe.whitelist()
def validate_item_code(item_code):
	"""
	Check that an item code exists in the Item master and belongs to
	the expected item group for wholesale gold inventory.
	Returns a dict so the frontend can show a helpful error message.
	"""
	if not item_code:
		return {"exists": False, "is_valid": False, "item_group": None}

	if not frappe.db.exists("Item", item_code):
		return {"item_code": item_code, "exists": False, "is_valid": False, "item_group": None}

	item_group = frappe.db.get_value("Item", item_code, "item_group")
	is_valid = item_group == "Wholesale Inventory (AU)"

	return {
		"item_code": item_code,
		"exists": True,
		"item_group": item_group,
		"is_valid": is_valid,
	}
