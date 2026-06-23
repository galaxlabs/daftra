import frappe
from frappe import _
from frappe.model.document import Document


class CreditType(Document):
    def validate(self):
        if not self.type_name:
            frappe.throw(_("Type name is required"))
        if self.default_credits and self.default_credits < 0:
            frappe.throw(_("Default credits cannot be negative"))
        if not self.unit_label:
            self.unit_label = "Credits"
