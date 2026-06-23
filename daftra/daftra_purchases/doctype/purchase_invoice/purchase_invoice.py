import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from daftra.api.project_api import sync_project_cost_center


class PurchaseInvoice(Document):
    def validate(self):
        if not self.invoice_date:
            frappe.throw(_("Invoice date is required"))
        if self.due_date and getdate(self.due_date) < getdate(self.invoice_date):
            frappe.throw(_("Due Date cannot be before Invoice Date"))
        subtotal = 0
        tax_amount = 0
        for row in self.get("items") or []:
            row.qty = flt(row.qty)
            row.rate = flt(row.rate)
            if row.qty <= 0:
                frappe.throw(_("Item quantity must be greater than zero"))
            row.amount = row.qty * row.rate
            row.vat_amount = row.amount * flt(getattr(row, "vat_rate", 0)) / 100
            subtotal += row.amount
            tax_amount += row.vat_amount
        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total = subtotal + tax_amount
        self.balance = self.total - flt(self.paid_amount)
        sync_project_cost_center(self)
