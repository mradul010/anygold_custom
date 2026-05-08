import frappe
from frappe.model.document import Document
from frappe.utils import flt

BASKET_TO_CUSTOMER_GROUP = {
    "Walk-in Retail": "Individual",
    "Pawn Shop": "Commercial",
    "Gold Shop": "Commercial",
    "Dealer": "Commercial",
    "Wholesale Buyer": "Commercial",
    "Swap Partner": "Commercial",
}

BASKET_TO_SUPPLIER_GROUP = {
    "Walk-in Retail": "Gold Seller - Retail",
    "Pawn Shop": "Gold Seller - Dealer",
    "Gold Shop": "Gold Seller - Dealer",
    "Dealer": "Gold Seller - Dealer",
    "Wholesale Buyer": "Gold Seller - Dealer",
    "Swap Partner": "Gold Swap Partner",
}


class AGContact(Document):

    def after_insert(self):
        self._newly_spawned = True
        self._spawn_parties()

    def on_update(self):
        # Skip KYC propagation on the initial insert (after_insert already handled it)
        if getattr(self, "_newly_spawned", False):
            return
        if self.linked_customer and self.linked_supplier:
            self._propagate_kyc()

    def _spawn_parties(self):
        address_name = None

        # 1. Create Address if enough data is provided
        if self.address_line_1 and self.city:
            address = frappe.new_doc("Address")
            address.address_title = self.display_name
            address.address_type = "Billing"
            address.address_line1 = self.address_line_1
            address.address_line2 = self.address_line_2 or ""
            address.city = self.city
            address.state = self.state or ""
            address.pincode = self.postcode or ""
            address.country = self.country or "Malaysia"
            address.insert(ignore_permissions=True, ignore_mandatory=True)
            address_name = address.name

        # 2. Create Contact
        contact = frappe.new_doc("Contact")
        contact.first_name = self.display_name
        contact.append("phone_nos", {
            "phone": self.phone_primary,
            "is_primary_phone": 1,
            "is_primary_mobile_no": 1,
        })
        if self.phone_secondary:
            contact.append("phone_nos", {"phone": self.phone_secondary})
        if self.email:
            contact.append("email_ids", {"email_id": self.email, "is_primary": 1})
        contact.insert(ignore_permissions=True)
        contact_name = contact.name

        # 3. Determine primary basket → Customer Group / Supplier Group
        primary_basket = self.baskets[0].basket if self.baskets else "Walk-in Retail"
        customer_group = BASKET_TO_CUSTOMER_GROUP.get(primary_basket, "Commercial")
        supplier_group = BASKET_TO_SUPPLIER_GROUP.get(primary_basket, "Gold Seller - Retail")

        if not frappe.db.exists("Customer Group", customer_group):
            customer_group = "All Customer Groups"
        if not frappe.db.exists("Supplier Group", supplier_group):
            supplier_group = "All Supplier Groups"

        # 4. Create Customer
        customer = frappe.new_doc("Customer")
        customer.customer_name = self.display_name
        customer.customer_type = self.entity_type
        customer.customer_group = customer_group
        customer.territory = "All Territories"
        customer.ag_contact = self.name
        customer.insert(ignore_permissions=True)

        # 5. Create Supplier
        supplier = frappe.new_doc("Supplier")
        supplier.supplier_name = self.display_name
        supplier.supplier_type = self.entity_type
        supplier.supplier_group = supplier_group
        supplier.ag_contact = self.name
        supplier.linked_customer = customer.name
        supplier.insert(ignore_permissions=True)

        # 6. Back-fill Customer.linked_supplier
        frappe.db.set_value(
            "Customer", customer.name, "linked_supplier", supplier.name,
            update_modified=False,
        )

        # 7. Create Bank Account if data provided
        if self.bank_name and self.bank_account_number:
            _create_bank_account(
                self.display_name, self.bank_name,
                self.bank_account_number, customer.name,
            )

        # 8. Wire Dynamic Links — single Address + Contact, three references each
        link_targets = [
            ("AG Contact", self.name),
            ("Customer", customer.name),
            ("Supplier", supplier.name),
        ]

        if address_name:
            for dt, dn in link_targets:
                frappe.get_doc({
                    "doctype": "Dynamic Link",
                    "parenttype": "Address",
                    "parent": address_name,
                    "parentfield": "links",
                    "link_doctype": dt,
                    "link_name": dn,
                }).insert(ignore_permissions=True)

        for dt, dn in link_targets:
            frappe.get_doc({
                "doctype": "Dynamic Link",
                "parenttype": "Contact",
                "parent": contact_name,
                "parentfield": "links",
                "link_doctype": dt,
                "link_name": dn,
            }).insert(ignore_permissions=True)

        # 9. Write linked refs back to this document (direct DB write to avoid recursion)
        frappe.db.set_value(
            "AG Contact", self.name,
            {"linked_customer": customer.name, "linked_supplier": supplier.name},
            update_modified=False,
        )
        self.linked_customer = customer.name
        self.linked_supplier = supplier.name

    def _propagate_kyc(self):
        before = self.get_doc_before_save()

        # Sync display_name → Customer + Supplier names
        if before and before.display_name != self.display_name:
            frappe.db.set_value(
                "Customer", self.linked_customer, "customer_name",
                self.display_name, update_modified=False,
            )
            frappe.db.set_value(
                "Supplier", self.linked_supplier, "supplier_name",
                self.display_name, update_modified=False,
            )

        # Sync entity_type → customer_type / supplier_type
        if before and before.entity_type != self.entity_type:
            frappe.db.set_value(
                "Customer", self.linked_customer, "customer_type",
                self.entity_type, update_modified=False,
            )
            frappe.db.set_value(
                "Supplier", self.linked_supplier, "supplier_type",
                self.entity_type, update_modified=False,
            )

        # Sync Contact (phone / email)
        contact_links = frappe.get_all(
            "Dynamic Link",
            filters={
                "link_doctype": "AG Contact",
                "link_name": self.name,
                "parenttype": "Contact",
            },
            fields=["parent"],
        )
        for row in contact_links:
            try:
                contact_doc = frappe.get_doc("Contact", row.parent)
                updated_phone = False
                for ph in contact_doc.phone_nos:
                    if ph.is_primary_phone:
                        ph.phone = self.phone_primary
                        updated_phone = True
                        break
                if not updated_phone:
                    contact_doc.append("phone_nos", {
                        "phone": self.phone_primary,
                        "is_primary_phone": 1,
                        "is_primary_mobile_no": 1,
                    })
                if self.email:
                    updated_email = False
                    for em in contact_doc.email_ids:
                        if em.is_primary:
                            em.email_id = self.email
                            updated_email = True
                            break
                    if not updated_email:
                        contact_doc.append("email_ids", {"email_id": self.email, "is_primary": 1})
                contact_doc.save(ignore_permissions=True)
            except Exception:
                frappe.log_error(frappe.get_traceback(), "AG Contact: Contact sync failed")

        # Sync Address if any address field changed
        if before and any([
            before.address_line_1 != self.address_line_1,
            before.address_line_2 != self.address_line_2,
            before.city != self.city,
            before.state != self.state,
            before.postcode != self.postcode,
            before.country != self.country,
        ]):
            address_links = frappe.get_all(
                "Dynamic Link",
                filters={
                    "link_doctype": "AG Contact",
                    "link_name": self.name,
                    "parenttype": "Address",
                },
                fields=["parent"],
            )
            if address_links:
                for row in address_links:
                    try:
                        addr = frappe.get_doc("Address", row.parent)
                        addr.address_line1 = self.address_line_1 or ""
                        addr.address_line2 = self.address_line_2 or ""
                        addr.city = self.city or ""
                        addr.state = self.state or ""
                        addr.pincode = self.postcode or ""
                        addr.country = self.country or "Malaysia"
                        addr.save(ignore_permissions=True)
                    except Exception:
                        frappe.log_error(frappe.get_traceback(), "AG Contact: Address sync failed")
            elif self.address_line_1 and self.city:
                # No address record yet — create one now
                address = frappe.new_doc("Address")
                address.address_title = self.display_name
                address.address_type = "Billing"
                address.address_line1 = self.address_line_1
                address.address_line2 = self.address_line_2 or ""
                address.city = self.city
                address.state = self.state or ""
                address.pincode = self.postcode or ""
                address.country = self.country or "Malaysia"
                address.insert(ignore_permissions=True, ignore_mandatory=True)
                for dt, dn in [
                    ("AG Contact", self.name),
                    ("Customer", self.linked_customer),
                    ("Supplier", self.linked_supplier),
                ]:
                    frappe.get_doc({
                        "doctype": "Dynamic Link",
                        "parenttype": "Address",
                        "parent": address.name,
                        "parentfield": "links",
                        "link_doctype": dt,
                        "link_name": dn,
                    }).insert(ignore_permissions=True)


def _create_bank_account(display_name, bank_name, bank_account_number, customer_name):
    try:
        bank_account = frappe.new_doc("Bank Account")
        bank_account.account_name = f"{display_name} - {bank_name}"
        bank_account.bank_account_no = bank_account_number
        bank_account.party_type = "Customer"
        bank_account.party = customer_name
        bank_rec = frappe.db.get_value("Bank", {"bank_name": bank_name}, "name")
        if bank_rec:
            bank_account.bank = bank_rec
        bank_account.insert(ignore_permissions=True, ignore_mandatory=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "AG Contact: Bank Account creation failed")
