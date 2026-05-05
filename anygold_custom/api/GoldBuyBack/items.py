import frappe
from frappe import _


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
