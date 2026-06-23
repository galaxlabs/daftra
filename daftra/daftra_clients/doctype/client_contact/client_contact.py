import frappe
from frappe import _
from frappe.model.document import Document


class ClientContact(Document):
    def validate(self):
        if not self.contact_name:
            frappe.throw(_("Contact name is required"))
        if not self.client:
            frappe.throw(_("Client is required"))
        if not self.phone and not self.email:
            frappe.throw(_("Either phone or email is required"))
        if self.is_primary:
            frappe.db.sql(
                """
                UPDATE `tabClient Contact`
                SET is_primary = 0
                WHERE client = %s AND name != %s
                """,
                (self.client, self.name or ""),
            )
