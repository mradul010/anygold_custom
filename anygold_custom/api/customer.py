import frappe

def create_supplier_for_customer(doc, method):
    # Check if supplier already exists
    existing_supplier = frappe.db.exists("Supplier", {
        "supplier_name": doc.customer_name
    })

    if existing_supplier:
        supplier_name = existing_supplier
    else:
        supplier = frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": doc.customer_name,
            "supplier_group": "All Supplier Groups",
            "supplier_type": "Individual" if doc.customer_type == "Individual" else "Company",
            "mobile_no": doc.mobile_no,
            "email_id": doc.email_id,
        })

        supplier.insert(ignore_permissions=True)
        supplier_name = supplier.name

        # Copy address & contacts
        copy_addresses(doc.name, supplier_name)
        copy_contacts(doc.name, supplier_name)

    # -------------------------
    # CREATE PARTY LINK
    # -------------------------
    #create_party_link(doc.name, supplier_name)

def copy_addresses(customer_name, supplier_name):
    address_links = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Customer",
            "link_name": customer_name,
            "parenttype": "Address"
        },
        fields=["parent"]
    )

    for link in address_links:
        address_name = link.parent

        # ✅ Check directly in DB (more reliable)
        exists = frappe.db.exists("Dynamic Link", {
            "parenttype": "Address",
            "parent": address_name,
            "link_doctype": "Supplier",
            "link_name": supplier_name
        })

        if exists:
            continue

        # ✅ Directly insert new Dynamic Link row
        frappe.get_doc({
            "doctype": "Dynamic Link",
            "parenttype": "Address",
            "parent": address_name,
            "parentfield": "links",
            "link_doctype": "Supplier",
            "link_name": supplier_name
        }).insert(ignore_permissions=True)


def copy_contacts(customer_name, supplier_name):
    contacts = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Customer",
            "link_name": customer_name,
            "parenttype": "Contact"
        },
        fields=["parent"]
    )

    for con in contacts:
        contact_doc = frappe.get_doc("Contact", con.parent)

        # Check if already linked to supplier
        already_linked = any(
            link.link_doctype == "Supplier" and link.link_name == supplier_name
            for link in contact_doc.links
        )

        if already_linked:
            continue

        # Append Supplier link
        contact_doc.append("links", {
            "link_doctype": "Supplier",
            "link_name": supplier_name
        })

        contact_doc.save(ignore_permissions=True)


def create_party_link(customer, supplier):
    # Avoid duplicate link
    exists = frappe.db.exists("Party Link", {
        "primary_party_type": "Customer",
        "primary_party": customer,
        "secondary_party_type": "Supplier",
        "secondary_party": supplier
    })

    if exists:
        return

    frappe.get_doc({
        "doctype": "Party Link",
        "primary_party_type": "Customer",
        "primary_party": customer,
        "secondary_party_type": "Supplier",
        "secondary_party": supplier
    }).insert(ignore_permissions=True)


import frappe

@frappe.whitelist()
def search_customers(txt=""):
    return frappe.get_all(
        "Customer",
        filters={
            "name": ["like", f"%{txt}%"]
        },
        fields=["name", "customer_name", "mobile_no"],
        limit=10
    )