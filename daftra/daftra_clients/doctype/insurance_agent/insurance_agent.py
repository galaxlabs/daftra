import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class InsuranceAgent(Document):
    def validate(self):
        if not self.agent_name:
            frappe.throw(_("Agent name is required"))
        self.commission_rate = flt(self.commission_rate)
        if self.commission_rate < 0 or self.commission_rate > 100:
            frappe.throw(_("Commission rate must be between 0 and 100"))
