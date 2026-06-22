import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class InvoicePayment(Document):
    def validate(self):
        if not self.payment_date:
            self.payment_date = nowdate()
        if flt(self.amount) <= 0:
            frappe.throw("Payment amount must be greater than zero")
        if self.sales_invoice:
            invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
            if flt(self.amount) > flt(invoice.balance) and flt(invoice.balance) > 0:
                frappe.throw("Payment amount cannot exceed invoice balance")

    def on_submit(self):
        if self.sales_invoice:
            invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
            invoice.paid_amount = flt(invoice.paid_amount) + flt(self.amount)
            invoice.balance = flt(invoice.total) - flt(invoice.paid_amount)
            invoice.status = "Paid" if invoice.balance <= 0 else "Submitted"
            invoice.save(ignore_permissions=True)
