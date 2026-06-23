import frappe
from frappe import _
from frappe.model.document import Document


class Supplier(Document):
    def validate(self):
        if not self.supplier_name:
            frappe.throw(_("Supplier name is required"))
        if not self.supplier_type:
            self.supplier_type = "Company"
