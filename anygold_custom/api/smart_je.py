import frappe
from frappe.utils import flt


def fire_smart_je(doc, method):
    """
    Fires on_submit of: Gold Buyback Submission, Payment Entry.
    Reads current AR/AP balances for the linked dual-party AG Contact and
    moves the residue balance directionally to the correct ledger side.
    """
    customer, supplier = _resolve_dual_party(doc)
    if not (customer and supplier):
        return

    company = doc.get("company") or frappe.defaults.get_user_default("Company")
    if not company:
        return

    ar_balance = _get_ar_balance(customer, company)
    ap_balance = _get_ap_balance(supplier, company)

    # Both sides already zero — nothing to net
    if ar_balance == 0 and ap_balance == 0:
        return

    # Already on the correct side with no residue on the other — no movement needed
    if ar_balance > 0 and ap_balance == 0:
        return
    if ap_balance > 0 and ar_balance == 0:
        return

    ar_account = _get_default_account(company, "default_receivable_account")
    ap_account = _get_default_account(company, "default_payable_account")

    if not ar_account or not ap_account:
        frappe.log_error(
            f"Smart JE skipped: missing default Receivable/Payable accounts for company {company}",
            "Smart JE",
        )
        return

    net = ar_balance - ap_balance
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.posting_date = doc.get("posting_date") or frappe.utils.today()
    je.company = company
    je.is_system_generated = 1          # native JE field
    je.ag_smart_je_source = f"{doc.doctype}:{doc.name}"

    if net > 0 and ap_balance > 0:
        # Net AR position — clear AP residue, move into AR
        amount = ap_balance
        je.append("accounts", {
            "account": ap_account,
            "party_type": "Supplier",
            "party": supplier,
            "debit_in_account_currency": amount,
            "credit_in_account_currency": 0,
        })
        je.append("accounts", {
            "account": ar_account,
            "party_type": "Customer",
            "party": customer,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": amount,
        })
        je.user_remark = f"Smart JE auto-netting: moved RM{amount} from AP to AR"

    elif net < 0 and ar_balance > 0:
        # Net AP position — clear AR residue, move into AP
        amount = ar_balance
        je.append("accounts", {
            "account": ar_account,
            "party_type": "Customer",
            "party": customer,
            "debit_in_account_currency": amount,
            "credit_in_account_currency": 0,
        })
        je.append("accounts", {
            "account": ap_account,
            "party_type": "Supplier",
            "party": supplier,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": amount,
        })
        je.user_remark = f"Smart JE auto-netting: moved RM{amount} from AR to AP"

    elif net == 0 and ar_balance > 0 and ap_balance > 0:
        # Fully settled — clear both sides simultaneously
        amount = ar_balance  # == ap_balance
        je.append("accounts", {
            "account": ar_account,
            "party_type": "Customer",
            "party": customer,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": amount,
        })
        je.append("accounts", {
            "account": ap_account,
            "party_type": "Supplier",
            "party": supplier,
            "debit_in_account_currency": amount,
            "credit_in_account_currency": 0,
        })
        je.user_remark = "Smart JE auto-netting: fully settled both sides"

    else:
        return  # No actionable case

    je.insert(ignore_permissions=True)
    je.submit()


def _resolve_dual_party(doc):
    """
    Returns (customer_name, supplier_name) for a dual-party AG Contact.
    Returns (None, None) for single-party contacts or documents with no AG Contact.
    """
    ag_contact = None

    # Direct ag_contact field on document
    if getattr(doc, "ag_contact", None):
        ag_contact = doc.ag_contact

    # Resolve via supplier field (future vouchers that post to Supplier side)
    elif getattr(doc, "supplier", None):
        ag_contact = frappe.db.get_value("Supplier", doc.supplier, "ag_contact")

    # Resolve via customer field (Gold Buyback currently links Customer)
    elif getattr(doc, "customer", None):
        ag_contact = frappe.db.get_value("Customer", doc.customer, "ag_contact")

    # Payment Entry: resolve via party_type + party
    elif doc.doctype == "Payment Entry":
        if doc.party_type == "Customer":
            ag_contact = frappe.db.get_value("Customer", doc.party, "ag_contact")
        elif doc.party_type == "Supplier":
            ag_contact = frappe.db.get_value("Supplier", doc.party, "ag_contact")

    if not ag_contact:
        return None, None

    linked = frappe.db.get_value(
        "AG Contact", ag_contact, ["linked_customer", "linked_supplier"], as_dict=True
    )
    if not linked or not linked.linked_customer or not linked.linked_supplier:
        return None, None

    return linked.linked_customer, linked.linked_supplier


def _get_ar_balance(customer, company):
    """Returns AR balance. Positive = customer owes AnyGold."""
    account = _get_default_account(company, "default_receivable_account")
    if not account:
        return 0.0
    result = frappe.db.sql("""
        SELECT SUM(debit_in_account_currency) - SUM(credit_in_account_currency)
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
          AND party = %s
          AND account = %s
          AND is_cancelled = 0
          AND docstatus = 1
    """, (customer, account))
    return flt(result[0][0]) if result and result[0][0] is not None else 0.0


def _get_ap_balance(supplier, company):
    """Returns AP balance. Positive = AnyGold owes supplier."""
    account = _get_default_account(company, "default_payable_account")
    if not account:
        return 0.0
    result = frappe.db.sql("""
        SELECT SUM(credit_in_account_currency) - SUM(debit_in_account_currency)
        FROM `tabGL Entry`
        WHERE party_type = 'Supplier'
          AND party = %s
          AND account = %s
          AND is_cancelled = 0
          AND docstatus = 1
    """, (supplier, account))
    return flt(result[0][0]) if result and result[0][0] is not None else 0.0


def _get_default_account(company, field):
    return frappe.db.get_value("Company", company, field)
