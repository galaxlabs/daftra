import frappe
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate, nowdate

class SalesInvoice(Document):
    def validate(self):
        if not self.invoice_date:
            self.invoice_date = nowdate()
        if self.payment_terms_days and not self.due_date:
            self.due_date = add_days(self.invoice_date, self.payment_terms_days)
        if self.due_date and getdate(self.due_date) < getdate(self.invoice_date):
            frappe.throw("Due Date cannot be before Invoice Date")

        subtotal = 0
        tax_amount = 0
        for row in self.get("items") or []:
            row.qty = flt(row.qty)
            row.rate = flt(row.rate)
            if row.qty <= 0:
                frappe.throw("Item quantity must be greater than zero")
            row.amount = row.qty * row.rate
            row.vat_amount = row.amount * flt(row.vat_rate) / 100
            subtotal += row.amount
            tax_amount += row.vat_amount

        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total = subtotal - flt(self.discount_amount) - flt(self.deposit_amount) + flt(self.adjustment_amount) + tax_amount
        if self.total < 0:
            frappe.throw("Invoice total cannot be negative")
        self.balance = self.total - flt(self.paid_amount)
        if self.balance <= 0 and self.total:
            self.status = "Paid"
        elif self.docstatus == 1:
            self.status = "Submitted"
