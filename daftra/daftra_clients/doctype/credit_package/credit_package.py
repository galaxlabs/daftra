import frappe
from frappe import _
from frappe.model.document import Document


class CreditPackage(Document):
    def validate(self):
        if not self.package_name:
            frappe.throw(_("Package name is required"))
        if self.credits is not None and self.credits < 0:
            frappe.throw(_("Credits cannot be negative"))
        if self.price is not None and self.price < 0:
            frappe.throw(_("Price cannot be negative"))
        if self.validity_days is not None and self.validity_days < 0:
            frappe.throw(_("Validity days cannot be negative"))
        if self.credit_type and not self.credits:
            self.credits = frappe.db.get_value("Credit Type", self.credit_type, "default_credits") or 0
