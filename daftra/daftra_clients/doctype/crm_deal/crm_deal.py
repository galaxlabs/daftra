import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CRMDeal(Document):
    def validate(self):
        if not self.deal_name:
            frappe.throw(_("Deal name is required"))
        self.expected_value = flt(self.expected_value)
        self.probability = flt(self.probability)
        if self.expected_value < 0:
            frappe.throw(_("Expected value cannot be negative"))
        if self.probability < 0 or self.probability > 100:
            frappe.throw(_("Probability must be between 0 and 100"))
        if not self.stage:
            self.stage = "Lead"
        if not self.assigned_to:
            self.assigned_to = frappe.session.user
