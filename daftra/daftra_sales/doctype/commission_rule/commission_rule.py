import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class CommissionRule(Document):
    def validate(self):
        self.rule_name = (self.rule_name or '').strip()
        self.commission_rate = flt(self.commission_rate)
        if not self.rule_name:
            frappe.throw(_('Rule Name is required'))
        if self.commission_rate < 0 or self.commission_rate > 100:
            frappe.throw(_('Commission Rate must be between 0 and 100'))
        if self.starts_on and self.ends_on and getdate(self.ends_on) < getdate(self.starts_on):
            frappe.throw(_('Ends On cannot be before Starts On'))
