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
            paid_amount = flt(invoice.paid_amount) + flt(self.amount)
            balance = flt(invoice.total) - paid_amount
            frappe.db.set_value("Sales Invoice", invoice.name, {
                "paid_amount": paid_amount,
                "balance": balance,
                "status": "Paid" if balance <= 0 else "Submitted",
            }, update_modified=True)
