import frappe
from frappe.utils import flt


@frappe.whitelist()
def list_ag_contacts(txt="", limit=21, offset=0):
    """
    Paginated list for the AG Contact list page.
    Returns up to `limit` rows starting at `offset`.
    Pass limit = PAGE_SIZE + 1 so the caller can detect hasMore.
    """
    limit  = min(int(limit), 100)
    offset = max(int(offset), 0)

    conditions = []
    values = {}

    if txt:
        conditions.append(
            "(ac.display_name LIKE %(txt)s"
            " OR ac.name LIKE %(txt)s"
            " OR ac.phone_primary LIKE %(txt)s"
            " OR ac.id_number LIKE %(txt)s)"
        )
        values["txt"] = f"%{txt}%"

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    return frappe.db.sql(
        f"""
        SELECT ac.name, ac.display_name, ac.entity_type, ac.is_active,
               ac.id_type, ac.id_number, ac.phone_primary,
               ac.linked_customer, ac.linked_supplier
        FROM `tabAG Contact` ac
        {where}
        ORDER BY ac.display_name
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        {**values, "limit": limit, "offset": offset},
        as_dict=True,
    )


@frappe.whitelist()
def search_ag_contacts(txt="", basket_filter=None):
    """
    Autocomplete search for AG Contacts.
    Used by the AGContactSelector Vue component.
    """
    conditions = ["ac.is_active = 1"]
    values = {}

    if txt:
        conditions.append(
            "(ac.display_name LIKE %(txt)s"
            " OR ac.name LIKE %(txt)s"
            " OR ac.phone_primary LIKE %(txt)s"
            " OR ac.id_number LIKE %(txt)s)"
        )
        values["txt"] = f"%{txt}%"

    where = " AND ".join(conditions)
    contacts = frappe.db.sql(
        f"""
        SELECT ac.name, ac.display_name, ac.phone_primary, ac.entity_type,
               ac.linked_customer, ac.linked_supplier,
               ac.id_type, ac.id_number, ac.bank_name, ac.bank_account_number
        FROM `tabAG Contact` ac
        WHERE {where}
        ORDER BY ac.display_name
        LIMIT 20
        """,
        values,
        as_dict=True,
    )

    if basket_filter:
        filtered = []
        for c in contacts:
            if frappe.db.exists(
                "AG Contact Basket Item",
                {"parent": c.name, "basket": basket_filter},
            ):
                filtered.append(c)
        return filtered

    return contacts


@frappe.whitelist()
def get_unified_balance(ag_contact):
    """
    Returns the net AR - AP balance for an AG Contact.
    Positive = customer owes AnyGold (AR side).
    Negative = AnyGold owes customer (AP side).
    """
    from anygold_custom.api.smart_je import _get_ar_balance, _get_ap_balance

    contact = frappe.get_doc("AG Contact", ag_contact)
    if not contact.linked_customer or not contact.linked_supplier:
        return {"balance": 0.0, "side": "none", "ar": 0.0, "ap": 0.0}

    company = frappe.defaults.get_user_default("Company")
    ar = _get_ar_balance(contact.linked_customer, company)
    ap = _get_ap_balance(contact.linked_supplier, company)
    net = ar - ap

    if net > 0:
        side = "AR"
    elif net < 0:
        side = "AP"
    else:
        side = "settled"

    return {"balance": net, "side": side, "ar": ar, "ap": ap}


@frappe.whitelist()
def get_unified_ledger(ag_contact, from_date=None, to_date=None):
    """
    Returns combined GL entries (Customer Debtors + Supplier Creditors) for an AG Contact,
    sorted by posting_date, with a running net balance.
    Positive running balance = AnyGold is owed. Negative = AnyGold owes.
    """
    from anygold_custom.api.smart_je import _get_default_account

    contact = frappe.get_doc("AG Contact", ag_contact)
    if not contact.linked_customer or not contact.linked_supplier:
        return []

    company = frappe.defaults.get_user_default("Company")
    ar_account = _get_default_account(company, "default_receivable_account")
    ap_account = _get_default_account(company, "default_payable_account")

    date_filter = ""
    params = {
        "customer": contact.linked_customer,
        "supplier": contact.linked_supplier,
        "ar_account": ar_account,
        "ap_account": ap_account,
    }

    if from_date:
        date_filter += " AND posting_date >= %(from_date)s"
        params["from_date"] = from_date
    if to_date:
        date_filter += " AND posting_date <= %(to_date)s"
        params["to_date"] = to_date

    ar_entries = frappe.db.sql(
        f"""
        SELECT posting_date, voucher_type, voucher_no,
               debit_in_account_currency  AS debit,
               credit_in_account_currency AS credit,
               remarks, 'AR' AS side
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
          AND party    = %(customer)s
          AND account  = %(ar_account)s
          AND is_cancelled = 0
          AND docstatus = 1
          {date_filter}
        """,
        params,
        as_dict=True,
    )

    ap_entries = frappe.db.sql(
        f"""
        SELECT posting_date, voucher_type, voucher_no,
               credit_in_account_currency AS debit,
               debit_in_account_currency  AS credit,
               remarks, 'AP' AS side
        FROM `tabGL Entry`
        WHERE party_type = 'Supplier'
          AND party    = %(supplier)s
          AND account  = %(ap_account)s
          AND is_cancelled = 0
          AND docstatus = 1
          {date_filter}
        """,
        params,
        as_dict=True,
    )

    # Combine, sort chronologically, compute running balance
    all_entries = sorted(
        list(ar_entries) + list(ap_entries),
        key=lambda x: (x["posting_date"], x["voucher_no"]),
    )
    running = 0.0
    for entry in all_entries:
        running += flt(entry["debit"]) - flt(entry["credit"])
        entry["running_balance"] = running

    return all_entries


@frappe.whitelist()
def get_contact_metrics(ag_contact):
    """
    Returns aggregated transaction metrics for the AG Contact Metrics tab.
    """
    from anygold_custom.api.smart_je import _get_ar_balance, _get_ap_balance

    contact = frappe.get_doc("AG Contact", ag_contact)
    if not contact.linked_customer or not contact.linked_supplier:
        return {}

    company = frappe.defaults.get_user_default("Company")

    buyback_row = frappe.db.sql(
        """
        SELECT COUNT(*) AS count,
               COALESCE(SUM(grand_total), 0)    AS total_rm,
               COALESCE(SUM(total_gross_weight), 0) AS total_grams
        FROM `tabGold Buyback Submission`
        WHERE customer = %(customer)s
          AND docstatus = 1
        """,
        {"customer": contact.linked_customer},
        as_dict=True,
    )

    last_txn = frappe.db.sql(
        """
        SELECT MAX(posting_date)
        FROM `tabGold Buyback Submission`
        WHERE customer = %(customer)s AND docstatus = 1
        """,
        {"customer": contact.linked_customer},
    )

    ar = _get_ar_balance(contact.linked_customer, company)
    ap = _get_ap_balance(contact.linked_supplier, company)
    totals = buyback_row[0] if buyback_row else {}

    return {
        "total_buyback_count": totals.get("count") or 0,
        "total_rm_bought": flt(totals.get("total_rm")),
        "total_grams_bought": flt(totals.get("total_grams")),
        "last_transaction_date": last_txn[0][0] if last_txn and last_txn[0][0] else None,
        "current_ar_balance": ar,
        "current_ap_balance": ap,
        "net_balance": ar - ap,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GOLD BUYBACK: create AG Contact from the new-customer modal
# ─────────────────────────────────────────────────────────────────────────────

# Maps the modal's "customer_type" selector to AG Contact Basket names
_CUSTOMER_TYPE_TO_BASKET = {
    "Individual": "Walk-in Retail",
    "Dealer":     "Dealer",
    "Company":    "Gold Shop",
}


@frappe.whitelist()
def create_ag_contact_from_gbb(data):
    """
    Creates an AG Contact from the Gold Buyback new-customer modal.

    Accepts the same payload shape as the old create_goldbuyback_customer so
    the frontend needs minimal changes.  Returns { success, duplicate, message, contact }.
    """
    import json

    if isinstance(data, str):
        data = json.loads(data)

    nationality    = data.get("nationality", "Malaysian")
    customer_type  = data.get("customer_type", "Individual")
    display_name   = (data.get("customer_name") or "").strip().upper()
    mobile         = (data.get("mobile_no") or "").strip()

    if not display_name:
        frappe.throw("Customer Name is required.")
    if not mobile:
        frappe.throw("Mobile Number is required.")

    # Resolve id_type + id_number
    if nationality == "Malaysian":
        id_type   = "Malaysian IC"
        id_number = (data.get("malaysian_id") or "").strip()
    else:
        id_type   = "Passport"
        id_number = (data.get("other_id_number") or "").strip()

    if not id_number:
        frappe.throw("ID Number is required.")

    # entity_type
    entity_type = "Company" if customer_type == "Company" else "Individual"

    # basket
    basket_name = _CUSTOMER_TYPE_TO_BASKET.get(customer_type, "Walk-in Retail")
    _ensure_basket_exists(basket_name)

    # Duplicate check by id_number
    existing_name = frappe.db.get_value("AG Contact", {"id_number": id_number}, "name")
    if existing_name:
        existing_doc = frappe.get_doc("AG Contact", existing_name)
        return {
            "success":   True,
            "duplicate": True,
            "message":   f"A contact with this ID already exists ({existing_name}).",
            "contact":   _format_contact_for_gbb(existing_doc),
        }

    doc = frappe.new_doc("AG Contact")
    doc.display_name        = display_name
    doc.entity_type         = entity_type
    doc.id_type             = id_type
    doc.id_number           = id_number
    doc.phone_primary       = mobile
    doc.bank_name           = (data.get("bank_name") or "").strip()
    doc.bank_account_number = (data.get("bank_account_number") or "").strip()
    if data.get("customer_photo"):
        doc.id_photo = data["customer_photo"]
    doc.append("baskets", {"basket": basket_name})
    doc.insert(ignore_permissions=True)

    return {
        "success":   True,
        "duplicate": False,
        "message":   "Contact created successfully.",
        "contact":   _format_contact_for_gbb(doc),
    }


def _ensure_basket_exists(basket_name):
    """Creates the AG Contact Basket master record if it doesn't exist yet."""
    if not frappe.db.exists("AG Contact Basket", basket_name):
        frappe.get_doc({
            "doctype":     "AG Contact Basket",
            "basket_name": basket_name,
            "is_active":   1,
        }).insert(ignore_permissions=True)


def _format_contact_for_gbb(doc):
    """Serialises an AG Contact into the shape the GBB modal expects."""
    return {
        "name":                doc.name,
        "customer_name":       doc.display_name,
        "display_name":        doc.display_name,
        "linked_customer":     doc.linked_customer,
        "linked_supplier":     doc.linked_supplier,
        "entity_type":         doc.entity_type,
        "id_type":             doc.id_type,
        "id_number":           doc.id_number,
        "phone_primary":       doc.phone_primary,
        "bank_name":           doc.bank_name,
        "bank_account_number": doc.bank_account_number,
        # Legacy keys the GBB modal currently reads from the old create endpoint
        "mobile_no":      doc.phone_primary,
        "ic_number":      doc.id_number if doc.id_type == "Malaysian IC" else "",
        "passport_number": doc.id_number if doc.id_type != "Malaysian IC" else "",
        "nationality":    "Malaysian" if doc.id_type == "Malaysian IC" else "Non-Malaysian / Foreigner",
        "customer_group": _CUSTOMER_TYPE_TO_BASKET.get("Individual", "Walk-in Retail"),
    }
