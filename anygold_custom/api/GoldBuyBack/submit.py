import frappe
from frappe import _
from frappe.utils import nowdate, nowtime, flt
from frappe.model.naming import make_autoname
import json
import re

@frappe.whitelist()
def get_company_payment_accounts(company=None):
    """Return dynamic payment accounts for a company for Gold Buyback UI."""
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

    # Try common company field first if present.
    company_default_bank = frappe.db.get_value("Company", company, "default_bank_account")
    if company_default_bank and any(b["value"] == company_default_bank for b in bank_accounts):
        default_bank = company_default_bank

    return {
        "company": company,
        "bank_accounts": bank_accounts,
        "default_bank_account": default_bank,
        "cash_account": _safe_get_account(get_cash_account, company, "Cash Account"),
        "customer_account": _safe_get_account(get_customer_account, company, "Customer Account"),
        "inventory_account": _safe_get_account(get_inventory_account, company, "Wholesale Inventory")
    }

@frappe.whitelist()
def submit_gold_buyback(data):
    """
    Submit gold buyback transaction by creating direct GL entries
    Bypasses standard ERPNext purchase receipt logic
    """
    try:
        # Parse the incoming data
        data = json.loads(data) if isinstance(data, str) else data

        # Extract data
        customer = data.get('customer')
        items = data.get('items', [])
        payment_method = data.get('payment_method')
        grand_total = flt(data.get('grand_total', 0))
        company = data.get('company', 'Anygold Sdn. Bhd.')
        posting_date = data.get('posting_date', nowdate())
        posting_time = data.get('posting_time', nowtime())

        if not customer or not items:
            frappe.throw(_("Customer and items are required"))

        # Get company details
        company_doc = frappe.get_doc("Company", company)
        default_currency = company_doc.default_currency

        # Create Journal Entry
        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "title": f"Gold Buyback - {customer.get('name')}",
            "voucher_type": "Journal Entry",
            "posting_date": posting_date,
            "company": company,
            "user_remark": f"Gold Buyback transaction for customer {customer.get('name')}",
            "accounts": []
        })

        total_debit = 0
        total_credit = 0

        # Process items - create inventory debit entries.
        # Credit side is handled by payment method rows below.
        for item in items:
            item_name = item.get('desc', 'Gold Item')
            purity = item.get('purity')
            gross_weight = flt(item.get('gross', 0))
            net_weight = flt(item.get('net', 0))
            rate = flt(item.get('rate', 0))
            amount = flt(item.get('amount', 0))

            if amount <= 0:
                continue

            # Debit a stock adjustment/clearing account.
            # Stock In Hand will be impacted by Stock Entry (not direct JE).
            inventory_account = get_inventory_account(company, "Gold")
            je.append("accounts", {
                "account": inventory_account,
                "debit_in_account_currency": amount,
                "debit": amount,
                "credit_in_account_currency": 0,
                "credit": 0,
                "party_type": "",
                "party": "",
                "cost_center": get_default_cost_center(company),
                "user_remark": f"Gold buyback clearing - {item_name} ({purity}) {net_weight}g"
            })
            total_debit += amount

        # Process payment method
        if payment_method == 'cash':
            # Cash Account (Credit)
            cash_account = get_cash_account(company)
            je.append("accounts", {
                "account": cash_account,
                "debit_in_account_currency": 0,
                "debit": 0,
                "credit_in_account_currency": grand_total,
                "credit": grand_total,
                "party_type": "",
                "party": "",
                "cost_center": get_default_cost_center(company),
                "user_remark": "Cash payment for gold buyback"
            })
            total_credit += grand_total

        elif payment_method == 'bank':
            # Bank Account (Credit)
            bank_account = get_bank_account(company, data.get('bank_account'))
            je.append("accounts", {
                "account": bank_account,
                "debit_in_account_currency": 0,
                "debit": 0,
                "credit_in_account_currency": grand_total,
                "credit": grand_total,
                "party_type": "",
                "party": "",
                "cost_center": get_default_cost_center(company),
                "user_remark": "Bank transfer payment for gold buyback"
            })
            total_credit += grand_total

        elif payment_method == 'custacct':
            # Customer Account (Credit to AR/AP)
            customer_account = get_customer_account(company)
            je.append("accounts", {
                "account": customer_account,
                "debit_in_account_currency": 0,
                "debit": 0,
                "credit_in_account_currency": grand_total,
                "credit": grand_total,
                "party_type": "Customer",
                "party": customer.get('name'),
                "cost_center": get_default_cost_center(company),
                "user_remark": f"Customer account payment - {customer.get('name')}"
            })
            total_credit += grand_total

        elif payment_method == 'mix':
            # Mixed payments
            mix_rows = data.get('mix_rows', [])
            for row in mix_rows:
                amount = flt(row.get('amount', 0))
                mode = row.get('mode')
                if amount <= 0:
                    continue

                if mode == 'Cash':
                    cash_account = get_cash_account(company)
                    je.append("accounts", {
                        "account": cash_account,
                        "debit_in_account_currency": 0,
                        "debit": 0,
                        "credit_in_account_currency": amount,
                        "credit": amount,
                        "party_type": "",
                        "party": "",
                        "cost_center": get_default_cost_center(company),
                        "user_remark": "Cash payment (mixed)"
                    })
                elif mode == 'Bank Transfer':
                    bank_account = get_bank_account(company, row.get('bank_account') or data.get('bank_account'))
                    je.append("accounts", {
                        "account": bank_account,
                        "debit_in_account_currency": 0,
                        "debit": 0,
                        "credit_in_account_currency": amount,
                        "credit": amount,
                        "party_type": "",
                        "party": "",
                        "cost_center": get_default_cost_center(company),
                        "user_remark": f"Bank transfer payment (mixed) - {bank_account}"
                    })
                elif mode == 'Customer Account':
                    customer_account = get_customer_account(company)
                    je.append("accounts", {
                        "account": customer_account,
                        "debit_in_account_currency": 0,
                        "debit": 0,
                        "credit_in_account_currency": amount,
                        "credit": amount,
                        "party_type": "Customer",
                        "party": customer.get('name'),
                        "cost_center": get_default_cost_center(company),
                        "user_remark": f"Customer account payment (mixed) - {customer.get('name')}"
                    })
                total_credit += amount

        # Validate totals
        if abs(total_debit - total_credit) > 0.01:
            frappe.throw(_("Journal Entry totals do not match: Debit {0}, Credit {1}").format(total_debit, total_credit))

        # Submit the Journal Entry
        je.insert(ignore_permissions=True)
        je.submit()

        # Create Stock Entry only for items physically in hand.
        # Not-in-hand purchases should be recorded without stock ledger movement.
        if not data.get("item_not_in_hand"):
            create_stock_entry(data, je.name)

        # Persist full UI payload for audit/debug and reporting
        submission_name = create_submission_record(data)

        return {
            "status": "success",
            "journal_entry": je.name,
            "submission": submission_name,
            "message": f"Gold buyback transaction completed. Journal Entry: {je.name}"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Gold Buyback Submission Error")
        frappe.throw(_("Error submitting gold buyback: {0}").format(str(e)))


def get_inventory_account(company, item_type="Gold"):
    """Get stock adjustment / clearing account for gold buyback JE."""
    # Prefer company configured stock adjustment account.
    stock_adjustment = frappe.db.get_value("Company", company, "stock_adjustment_account")
    if stock_adjustment:
        return stock_adjustment

    # Try to find a stock adjustment account by name.
    accounts = frappe.get_all("Account",
        filters={
            "company": company,
            "account_name": ["like", "%Stock Adjustment%"],
            "is_group": 0
        },
        fields=["name"],
        limit=1
    )
    if accounts:
        return accounts[0].name

    # Try to find any expense account as a fallback clearing account.
    accounts = frappe.get_all("Account",
        filters={
            "company": company,
            "account_type": "Expense Account",
            "is_group": 0
        },
        fields=["name"],
        limit=1
    )
    if accounts:
        return accounts[0].name

    # Fallback
    frappe.throw(_("No stock adjustment/clearing account found for company {0}").format(company))


def _safe_get_account(getter_fn, company, fallback_label):
    """Return account if available; fallback label if not configured."""
    try:
        return getter_fn(company)
    except Exception:
        return fallback_label


def get_cogs_account(company):
    """Get Cost of Goods Sold account"""
    accounts = frappe.get_all("Account",
        filters={
            "company": company,
            "account_name": ["like", "%Cost of Goods Sold%"],
            "is_group": 0
        },
        fields=["name"],
        limit=1
    )
    if accounts:
        return accounts[0].name

    # Try direct expense account
    accounts = frappe.get_all("Account",
        filters={
            "company": company,
            "account_type": "Expense Account",
            "is_group": 0
        },
        fields=["name"],
        limit=1
    )
    if accounts:
        return accounts[0].name

    frappe.throw(_("No COGS account found for company {0}").format(company))


def get_cash_account(company):
    """Get cash account"""
    accounts = frappe.get_all("Account",
        filters={
            "company": company,
            "account_type": "Cash",
            "is_group": 0
        },
        fields=["name"],
        limit=1
    )
    if accounts:
        return accounts[0].name

    frappe.throw(_("No cash account found for company {0}").format(company))


def get_bank_account(company, bank_account=None):
    """Get bank account"""
    if bank_account:
        # Validate the account exists
        if frappe.db.exists("Account", bank_account):
            return bank_account

    accounts = frappe.get_all("Account",
        filters={
            "company": company,
            "account_type": "Bank",
            "is_group": 0
        },
        fields=["name"],
        limit=1
    )
    if accounts:
        return accounts[0].name

    frappe.throw(_("No bank account found for company {0}").format(company))


def get_customer_account(company):
    """Get customer receivable account"""
    accounts = frappe.get_all("Account",
        filters={
            "company": company,
            "account_type": "Receivable",
            "is_group": 0
        },
        fields=["name"],
        limit=1
    )
    if accounts:
        return accounts[0].name

    frappe.throw(_("No receivable account found for company {0}").format(company))


def get_default_cost_center(company):
    """Get default cost center"""
    # Prefer company-level default if configured.
    company_default = frappe.db.get_value("Company", company, "cost_center")
    if company_default:
        return company_default

    # Fallback to any leaf cost center for this company.
    cost_centers = frappe.get_all(
        "Cost Center",
        filters={
            "company": company,
            "is_group": 0
        },
        fields=["name"],
        order_by="modified desc",
        limit=1
    )
    if cost_centers:
        return cost_centers[0].name

    frappe.throw(_("No cost center found for company {0}").format(company))


def create_stock_entry(data, je_name):
    """Create stock entry for inventory tracking"""
    try:
        items = data.get('items', [])
        company = data.get('company', 'Anygold Sdn. Bhd.')

        if not items:
            return

        warehouse = get_default_warehouse(company)
        if not warehouse:
            frappe.throw(_("No warehouse found for company {0}").format(company))

        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": data.get('posting_date', nowdate()),
            "posting_time": data.get('posting_time', nowtime()),
            "purpose": "Material Receipt",
            "items": []
        })

        for item in items:
            item_name = item.get('desc', 'Gold Item')
            purity = item.get('purity')
            net_weight = flt(item.get('net', 0))
            amount = flt(item.get('amount', 0))

            if net_weight <= 0:
                continue

            # Find or create item
            item_code = get_or_create_item(item_name, purity)
            resolved_item_name = frappe.db.get_value("Item", item_code, "item_name") or item_name
            stock_uom = frappe.db.get_value("Item", item_code, "stock_uom") or "Nos"
            qty = net_weight
            valuation_rate = flt(item.get('rate', 0)) or (amount / qty if qty else 0)

            se.append("items", {
                "item_code": item_code,
                "item_name": resolved_item_name,
                "qty": qty,
                "uom": stock_uom,
                "stock_uom": stock_uom,
                "conversion_factor": 1,
                "transfer_qty": qty,
                "t_warehouse": warehouse,
                "valuation_rate": valuation_rate,
                "basic_rate": valuation_rate,
                "basic_amount": amount,
                "amount": amount,
                "description": f"{resolved_item_name} - {net_weight}g"
            })

        if se.items:
            se.insert(ignore_permissions=True)
            se.submit()
        else:
            frappe.throw(_("No stock rows were generated from submitted items"))

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Stock Entry Creation Error")
        frappe.throw(_("Stock Entry creation failed: {0}").format(str(e)))


def create_submission_record(data):
    """Create Gold Buyback Submission record with all page fields."""
    customer = data.get("customer") or {}
    items = data.get("items") or []
    mix_rows = data.get("mix_rows") or []

    posting_date = data.get("posting_date", nowdate())
    posting_time = data.get("posting_time", nowtime())

    doc = frappe.get_doc({
        "doctype": "Gold Buyback Submission",
        "posting_date": posting_date,
        "posting_time": posting_time,
        "edit_posting_datetime": 1 if data.get("edit_posting_datetime") else 0,
        "item_not_in_hand": 1 if data.get("item_not_in_hand") else 0,
        "customer_name": customer.get("name"),
        "customer_ic": customer.get("ic"),
        "customer_mobile": customer.get("mobile"),
        "customer_type": customer.get("type"),
        "payment_method": data.get("payment_method"),
        "bank_account": data.get("bank_account"),
        "default_bag": data.get("default_bag"),
        "company": data.get("company", "Anygold Sdn. Bhd."),
        "total_gross_weight": flt(data.get("total_gross_weight", 0)),
        "total_net_weight": flt(data.get("total_net_weight", 0)),
        "total_amount": flt(data.get("total_amount", 0)),
        "discount": flt(data.get("discount", 0)),
        "rounding": 1 if data.get("rounding") else 0,
        "grand_total": flt(data.get("grand_total", 0)),
        "total_xau": flt(data.get("total_xau", 0)),
        "customer_account_amount": flt(data.get("customer_account_amount", 0)),
        "projected_balance": flt(data.get("projected_balance", 0)),
        "status": data.get("status") or "submitted",
        "payload_json": json.dumps(data, default=str)
    })

    for item in items:
        deductions = item.get("deds") or []
        doc.append("items", {
            "description": item.get("desc"),
            "purity": item.get("purity"),
            "gross_weight": flt(item.get("gross", 0)),
            "net_weight": flt(item.get("net", 0)),
            "rate": flt(item.get("rate", 0)),
            "amount": flt(item.get("amount", 0)),
            "lock_id": item.get("lockId"),
            "overage_ack": 1 if item.get("overageAck") else 0,
            "bag": item.get("bag"),
            "deductions_weight": sum(flt(d.get("w", 0)) for d in deductions),
            "deductions_json": json.dumps(deductions, default=str)
        })

    for row in mix_rows:
        doc.append("mix_payments", {
            "mode": row.get("mode"),
            "amount": flt(row.get("amount", 0))
        })

    # Force robust naming to avoid duplicate literal autoname collisions.
    # Example: GBB-2026-00001
    for _ in range(3):
        doc.name = make_autoname("GBB-.YYYY.-.#####")
        if not frappe.db.exists("Gold Buyback Submission", doc.name):
            break
    doc.flags.name_set = True
    doc.insert(ignore_permissions=True)
    return doc.name


def get_or_create_item(item_name, purity=None):
    """Get/create purity-specific stock item variant.

    Example:
    - CINCIN + 916  -> GBB-CINCIN-916 (Item Name: CINCIN (916))
    - CINCIN + 9999 -> GBB-CINCIN-9999 (Item Name: CINCIN (9999))
    """
    base_name = (item_name or "Gold Item").strip()
    purity_key = _normalize_purity_key(purity)
    item_code_base = _build_purity_variant_item_code(base_name, purity_key)
    item_name_variant = _build_purity_variant_item_name(base_name, purity_key)

    # First preference: deterministic purity variant code
    if frappe.db.exists("Item", item_code_base):
        return item_code_base

    # Backward compatibility: if same purity variant name already exists, reuse it
    existing_by_name = frappe.db.get_value("Item", {"item_name": item_name_variant}, "name")
    if existing_by_name:
        return existing_by_name

    # Create new purity-specific item variant
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
    code = f"GBB-{base_slug}-{purity_key}"
    return code[:140]


def _build_purity_variant_item_name(base_name, purity_key):
    name = f"{(base_name or 'Gold Item').strip()} ({purity_key})"
    return name[:140]


def get_default_warehouse(company):
    """Resolve a usable target warehouse for material receipt."""
    default_wh = frappe.db.get_single_value("Stock Settings", "default_warehouse")
    if default_wh:
        wh_company = frappe.db.get_value("Warehouse", default_wh, "company")
        if not wh_company or wh_company == company:
            return default_wh

    company_default = frappe.db.get_value("Company", company, "default_warehouse")
    if company_default:
        return company_default

    warehouses = frappe.get_all(
        "Warehouse",
        filters={"company": company, "is_group": 0},
        fields=["name"],
        order_by="modified desc",
        limit=1
    )
    return warehouses[0].name if warehouses else None


def get_weight_uom():
    """Prefer Gram if present, otherwise fallback to a valid UOM."""
    if frappe.db.exists("UOM", "Gram"):
        return "Gram"
    if frappe.db.exists("UOM", "Nos"):
        return "Nos"
    uom = frappe.get_all("UOM", fields=["name"], limit=1)
    return uom[0].name if uom else "Nos"


def get_default_item_group():
    """Pick a valid non-group Item Group for dynamic item creation."""
    if frappe.db.exists("Item Group", "Gold"):
        return "Gold"
    groups = frappe.get_all(
        "Item Group",
        filters={"is_group": 0},
        fields=["name"],
        order_by="modified desc",
        limit=1
    )
    if groups:
        return groups[0].name
    frappe.throw(_("No Item Group found to create stock items"))
