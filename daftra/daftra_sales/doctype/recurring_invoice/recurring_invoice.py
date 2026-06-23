import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class RecurringInvoice(Document):
    def validate(self):
        if not self.client:
            frappe.throw(_('Client is required'))
        if not self.frequency:
            frappe.throw(_('Frequency is required'))
        if not self.start_date:
            frappe.throw(_('Start Date is required'))
        if self.end_date and getdate(self.end_date) < getdate(self.start_date):
            frappe.throw(_('End Date cannot be before Start Date'))
        if self.total_amount is None or self.total_amount <= 0:
            frappe.throw(_('Amount must be greater than zero'))
        self.status = self.status or 'Active'
        self.next_invoice_date = self.next_invoice_date or self.start_date
