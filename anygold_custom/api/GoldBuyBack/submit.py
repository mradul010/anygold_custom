import frappe
from frappe import _
from frappe.utils import nowdate, nowtime, flt
import json
import re


@frappe.whitelist()
def get_next_doc_no():
	"""
	Peek at the next Gold Buyback Submission document number without consuming it.
	Reads the current counter from tabSeries and returns next = current + 1.
	The actual name is assigned by Frappe on insert, so this is a preview only.
	"""
	from frappe.utils import now_datetime
	year = str(now_datetime().year)
	prefix = f"GBB-{year}-"
	# tabSeries has only `name` and `current` — no `creation` column.
	# frappe.db.get_value adds ORDER BY creation and crashes on this table,
	# so query it directly with raw SQL.
	result = frappe.db.sql("SELECT `current` FROM `tabSeries` WHERE `name` = %s", (prefix,))
	current = int(result[0][0]) if result else 0
	next_seq = current + 1
	return f"{prefix}{str(next_seq).zfill(5)}"


@frappe.whitelist()
def get_company_payment_accounts(company=None):
	"""Return payment accounts for a company for the Gold Buyback UI."""
	company = company or frappe.defaults.get_global_default("company")
	if not company:
		frappe.throw(_("Please set a default company."))

	bank_rows = frappe.get_all(
		"Account",
		filters={"company": company, "account_type": "Bank", "is_group": 0},
		fields=["name", "account_name"],
		order_by="account_name asc"
	)
	bank_accounts = []
	for row in bank_rows:
		label = row.account_name or row.name
		if row.account_name and row.account_name != row.name:
			label = f"{row.account_name} ({row.name})"
		bank_accounts.append({"value": row.name, "label": label})

	default_bank = None
	if bank_accounts:
		default_bank = bank_accounts[0]["value"]

	company_default_bank = frappe.db.get_value("Company", company, "default_bank_account")
	if company_default_bank and any(b["value"] == company_default_bank for b in bank_accounts):
		default_bank = company_default_bank

	return {
		"company": company,
		"bank_accounts": bank_accounts,
		"default_bank_account": default_bank,
		"cash_account": _safe_get_account(get_cash_account, company, "Cash Account"),
		"customer_account": _safe_get_account(get_customer_account, company, "Customer Account"),
		"inventory_account": _safe_get_account(
			lambda c: get_wholesale_inventory_account(c, not_in_hand=False),
			company,
			"Wholesale Inventory"
		)
	}


@frappe.whitelist()
def submit_gold_buyback(data):
	"""
	Create and submit a Gold Buyback Submission document.
	The controller (StockController subclass) posts GL + SLE on submit.
	No Journal Entry or Stock Entry is created.
	"""
	try:
		data = json.loads(data) if isinstance(data, str) else data

		customer = data.get("customer")
		items = data.get("items", [])
		payment_method = data.get("payment_method")
		grand_total = flt(data.get("grand_total", 0))
		company = data.get("company", "Anygold Sdn. Bhd.")
		posting_date = data.get("posting_date", nowdate())
		posting_time = data.get("posting_time", nowtime())
		item_not_in_hand = bool(data.get("item_not_in_hand"))

		if not customer or not items:
			frappe.throw(_("Customer and items are required"))

		cost_center = get_default_cost_center(company)
		inventory_account = get_wholesale_inventory_account(company, not_in_hand=item_not_in_hand)

		# Resolve the payment account(s) up front so the controller never has to look them up.
		mix_rows = data.get("mix_rows", [])
		payment_account = None

		if payment_method == "cash":
			payment_account = get_cash_account(company)
		elif payment_method == "bank":
			payment_account = get_bank_account(company, data.get("bank_account"))
		elif payment_method == "custacct":
			payment_account = get_customer_account(company)
		elif payment_method == "mix":
			for row in mix_rows:
				mode = row.get("mode")
				if mode == "Cash":
					row["_account"] = get_cash_account(company)
				elif mode == "Bank Transfer":
					row["_account"] = get_bank_account(company, row.get("bank_account") or data.get("bank_account"))
				elif mode == "Customer Account":
					row["_account"] = get_customer_account(company)

		# Build document
		doc = frappe.get_doc({
			"doctype": "Gold Buyback Submission",
			"posting_date": posting_date,
			"posting_time": posting_time,
			"edit_posting_datetime": 1 if data.get("edit_posting_datetime") else 0,
			"item_not_in_hand": 1 if item_not_in_hand else 0,
			# Customer
			"customer": customer.get("name"),
			"customer_name": customer.get("name"),
			"customer_ic": customer.get("ic"),
			"customer_mobile": customer.get("mobile"),
			"customer_type": customer.get("type"),
			# Payment
			"payment_method": payment_method,
			"bank_account": data.get("bank_account"),
			"default_bag": data.get("default_bag"),
			"company": company,
			# Accounting — pre-resolved so the controller can post without extra DB queries.
			"inventory_account": inventory_account,
			"cost_center": cost_center,
			"payment_account": payment_account,
			# Totals
			"total_gross_weight": flt(data.get("total_gross_weight", 0)),
			"total_net_weight": flt(data.get("total_net_weight", 0)),
			"total_amount": flt(data.get("total_amount", 0)),
			"discount": flt(data.get("discount", 0)),
			"rounding": 1 if data.get("rounding") else 0,
			"grand_total": grand_total,
			"total_xau": flt(data.get("total_xau", 0)),
			"customer_account_amount": flt(data.get("customer_account_amount", 0)),
			"projected_balance": flt(data.get("projected_balance", 0)),
			"status": "submitted",
			"payload_json": json.dumps(data, default=str),
			"items": [],
			"mix_payments": []
		})

		# Append item rows.
		# item_code is pre-resolved by the frontend as WS-{purity}-N or WS-{purity}-EBTS.
		# warehouse is pre-resolved by the frontend; fall back to bag resolution if absent.
		for item in items:
			net_weight = flt(item.get("net", 0))
			if net_weight <= 0:
				continue

			item_code = item.get("item_code") or ""
			if not item_code:
				purity = item.get("purity") or ""
				deds   = item.get("deds") or []
				suffix = "EBTS" if deds else "N"
				item_code = f"WS-{purity}-{suffix}" if purity else ""
			if not item_code or not frappe.db.exists("Item", item_code):
				frappe.throw(_("Item {0} not found in Item master. Please create it before submitting.").format(item_code or _("unknown")))

			warehouse = item.get("warehouse") or None
			if not warehouse:
				bag = item.get("bag") or data.get("default_bag")
				warehouse = resolve_warehouse_for_bag(bag, company, item_not_in_hand)

			deductions = item.get("deds") or []
			doc.append("items", {
				"description": item.get("desc"),
				"purity": item.get("purity"),
				"gross_weight": flt(item.get("gross", 0)),
				"net_weight": net_weight,
				"rate": flt(item.get("rate", 0)),
				"amount": flt(item.get("amount", 0)),
				"item_code": item_code,
				"warehouse": warehouse,
				"lock_id": item.get("lockId"),
				"overage_ack": 1 if item.get("overageAck") else 0,
				"bag": item.get("bag") or data.get("default_bag"),
				"deductions_weight": sum(flt(d.get("w", 0)) for d in deductions),
				"deductions_json": json.dumps(deductions, default=str),
			})

		# Append mix-payment rows with resolved accounts.
		for row in mix_rows:
			if flt(row.get("amount", 0)) <= 0:
				continue
			doc.append("mix_payments", {
				"mode": row.get("mode"),
				"amount": flt(row.get("amount", 0)),
				"account": row.get("_account"),
			})

		doc.insert(ignore_permissions=True)
		doc.submit()

		return {
			"status": "success",
			"submission": doc.name,
			"message": f"Gold buyback completed. Reference: {doc.name}"
		}

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Gold Buyback Submission Error")
		raise


# ── Account helpers ─────────────────────────────────────────────────────────────


def get_wholesale_inventory_account(company, not_in_hand=False):
	"""Return the correct inventory GL account based on whether the item is in hand."""
	pattern = "Not In Hand" if not_in_hand else "Wholesale Inventory"
	accounts = frappe.get_all("Account",
		filters={"company": company, "account_name": ["like", f"%{pattern}%"], "is_group": 0},
		fields=["name"], limit=1
	)
	if accounts:
		return accounts[0].name

	# Fallback chain for in-hand: Stock In Hand → company stock_adjustment_account
	if not not_in_hand:
		accounts = frappe.get_all("Account",
			filters={"company": company, "account_name": ["like", "%Stock In Hand%"], "is_group": 0},
			fields=["name"], limit=1
		)
		if accounts:
			return accounts[0].name
		stock_adj = frappe.db.get_value("Company", company, "stock_adjustment_account")
		if stock_adj:
			return stock_adj

	label = _("Not In Hand") if not_in_hand else _("Wholesale Inventory")
	frappe.throw(_("No {0} account found for company {1}").format(label, company))


def get_cash_account(company):
	accounts = frappe.get_all("Account",
		filters={"company": company, "account_type": "Cash", "is_group": 0},
		fields=["name"], limit=1
	)
	if accounts:
		return accounts[0].name
	frappe.throw(_("No cash account found for company {0}").format(company))


def get_bank_account(company, bank_account=None):
	if bank_account and frappe.db.exists("Account", bank_account):
		return bank_account
	accounts = frappe.get_all("Account",
		filters={"company": company, "account_type": "Bank", "is_group": 0},
		fields=["name"], limit=1
	)
	if accounts:
		return accounts[0].name
	frappe.throw(_("No bank account found for company {0}").format(company))


def get_customer_account(company):
	accounts = frappe.get_all("Account",
		filters={"company": company, "account_type": "Receivable", "is_group": 0},
		fields=["name"], limit=1
	)
	if accounts:
		return accounts[0].name
	frappe.throw(_("No receivable account found for company {0}").format(company))


def get_default_cost_center(company):
	cc = frappe.db.get_value("Company", company, "cost_center")
	if cc:
		return cc
	cost_centers = frappe.get_all("Cost Center",
		filters={"company": company, "is_group": 0},
		fields=["name"], order_by="modified desc", limit=1
	)
	if cost_centers:
		return cost_centers[0].name
	frappe.throw(_("No cost center found for company {0}").format(company))


def _safe_get_account(getter_fn, company, fallback_label):
	try:
		return getter_fn(company)
	except Exception:
		return fallback_label


# ── Warehouse helpers ────────────────────────────────────────────────────────────


def resolve_warehouse_for_bag(bag_name, company, not_in_hand=False):
	"""Map a bag display-name (or not-in-hand flag) to a Warehouse document name."""
	if not_in_hand:
		warehouses = frappe.get_all("Warehouse",
			filters={"company": company, "warehouse_name": ["like", "%Not In Hand%"], "is_group": 0},
			fields=["name"], limit=1
		)
		if warehouses:
			return warehouses[0].name
		return get_default_warehouse(company)

	if bag_name:
		# Exact document-name match (e.g., "WS-Main Bag - AGSB")
		if frappe.db.exists("Warehouse", bag_name):
			return bag_name
		# Match by warehouse_name field (e.g., "WS-Main Bag")
		warehouses = frappe.get_all("Warehouse",
			filters={"company": company, "warehouse_name": ["like", f"%{bag_name}%"], "is_group": 0},
			fields=["name"], limit=1
		)
		if warehouses:
			return warehouses[0].name

	return get_default_warehouse(company)


def get_default_warehouse(company):
	default_wh = frappe.db.get_single_value("Stock Settings", "default_warehouse")
	if default_wh:
		wh_company = frappe.db.get_value("Warehouse", default_wh, "company")
		if not wh_company or wh_company == company:
			return default_wh

	company_default = frappe.db.get_value("Company", company, "default_warehouse")
	if company_default:
		return company_default

	warehouses = frappe.get_all("Warehouse",
		filters={"company": company, "is_group": 0},
		fields=["name"], order_by="modified desc", limit=1
	)
	return warehouses[0].name if warehouses else None


# ── Item helpers ─────────────────────────────────────────────────────────────────


def get_or_create_item(item_name, purity=None):
	"""Return an Item document name for the given description + purity combination.

	Item codes follow the pattern GBB-{SLUG}-{PURITY}, e.g. GBB-CINCIN-916.
	"""
	base_name = (item_name or "Gold Item").strip()
	purity_key = _normalize_purity_key(purity)
	item_code_base = _build_purity_variant_item_code(base_name, purity_key)
	item_name_variant = _build_purity_variant_item_name(base_name, purity_key)

	if frappe.db.exists("Item", item_code_base):
		return item_code_base

	existing_by_name = frappe.db.get_value("Item", {"item_name": item_name_variant}, "name")
	if existing_by_name:
		return existing_by_name

	item_group = get_default_item_group()
	stock_uom = get_weight_uom()
	item_code = item_code_base
	if frappe.db.exists("Item", item_code):
		item_code = f"{item_code_base}-{frappe.generate_hash(length=4)}"

	item_doc = frappe.get_doc({
		"doctype": "Item",
		"item_code": item_code,
		"item_name": item_name_variant,
		"item_group": item_group,
		"stock_uom": stock_uom,
		"is_stock_item": 1,
		"valuation_method": "Moving Average",
		"description": f"{base_name} - Purity {purity_key}"
	})
	item_doc.insert(ignore_permissions=True)
	return item_doc.name


def _normalize_purity_key(purity):
	key = re.sub(r"[^A-Za-z0-9]+", "", str(purity or "").strip().upper())
	return key or "UNK"


def _slugify_for_item_code(text, max_len=80):
	slug = re.sub(r"[^A-Za-z0-9]+", "-", str(text or "").strip().upper()).strip("-")
	if not slug:
		slug = "ITEM"
	return slug[:max_len]


def _build_purity_variant_item_code(base_name, purity_key):
	base_slug = _slugify_for_item_code(base_name)
	return f"GBB-{base_slug}-{purity_key}"[:140]


def _build_purity_variant_item_name(base_name, purity_key):
	return f"{(base_name or 'Gold Item').strip()} ({purity_key})"[:140]


def get_weight_uom():
	if frappe.db.exists("UOM", "Gram"):
		return "Gram"
	if frappe.db.exists("UOM", "Nos"):
		return "Nos"
	uom = frappe.get_all("UOM", fields=["name"], limit=1)
	return uom[0].name if uom else "Nos"


def get_default_item_group():
	"""Return a valid non-group Item Group, preferring Wholesale Inventory > Gold > first available."""
	for preferred in ("Wholesale Inventory", "Gold"):
		if frappe.db.exists("Item Group", preferred):
			return preferred
	groups = frappe.get_all("Item Group",
		filters={"is_group": 0}, fields=["name"], order_by="modified desc", limit=1
	)
	if groups:
		return groups[0].name
	frappe.throw(_("No Item Group found to create stock items"))
