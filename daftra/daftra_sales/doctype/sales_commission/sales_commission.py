import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SalesCommission(Document):
    def validate(self):
        self.commission_rate = flt(self.commission_rate)
        self.commission_amount = flt(self.commission_amount)
        self.status = self.status or 'Pending'
        if self.sales_person and not frappe.db.exists('User', self.sales_person):
            frappe.throw(_('Sales Person must be a valid user'))
        if self.commission_rate < 0 or self.commission_rate > 100:
            frappe.throw(_('Rate must be between 0 and 100'))
        if self.commission_amount < 0:
            frappe.throw(_('Commission Amount cannot be negative'))
