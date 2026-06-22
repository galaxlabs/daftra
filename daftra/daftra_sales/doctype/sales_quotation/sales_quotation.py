import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate

class SalesQuotation(Document):
    def validate(self):
        if self.valid_till and self.quotation_date and getdate(self.valid_till) < getdate(self.quotation_date):
            frappe.throw("Valid Till cannot be before Quotation Date")

        subtotal = 0
        for row in self.get("items") or []:
            row.qty = flt(row.qty)
            row.rate = flt(row.rate)
            if row.qty <= 0:
                frappe.throw("Item quantity must be greater than zero")
            row.amount = row.qty * row.rate
            subtotal += row.amount

        self.subtotal = subtotal
        self.total = subtotal - flt(self.discount_amount) + flt(self.tax_amount)
        if self.total < 0:
            frappe.throw("Quotation total cannot be negative")
