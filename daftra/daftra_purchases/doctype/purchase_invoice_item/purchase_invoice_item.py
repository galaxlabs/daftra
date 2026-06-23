import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PurchaseInvoiceItem(Document):
    def validate(self):
        self.qty = flt(self.qty)
        self.rate = flt(self.rate)
        self.vat_rate = flt(self.vat_rate)
        if self.qty <= 0:
            frappe.throw(_("Quantity must be greater than zero"))
        if self.rate < 0:
            frappe.throw(_("Rate cannot be negative"))
        self.amount = self.qty * self.rate
        self.vat_amount = self.amount * self.vat_rate / 100
