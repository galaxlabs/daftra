import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class SupplierPayment(Document):
    def validate(self):
        if not self.payment_date:
            self.payment_date = nowdate()
        if flt(self.amount) <= 0:
            frappe.throw("Payment amount must be greater than zero")

    def on_submit(self):
        if self.purchase_invoice:
            invoice = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
            paid_amount = flt(invoice.paid_amount) + flt(self.amount)
            frappe.db.set_value("Purchase Invoice", invoice.name, {
                "paid_amount": paid_amount,
                "status": "Paid" if paid_amount >= flt(invoice.total) else "Submitted",
            }, update_modified=True)
