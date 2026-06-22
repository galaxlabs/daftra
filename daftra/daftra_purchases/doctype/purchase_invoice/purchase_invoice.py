import frappe
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate, nowdate

class PurchaseInvoice(Document):
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
        self.total = subtotal + tax_amount
        if self.total < 0:
            frappe.throw("Purchase total cannot be negative")
        if flt(self.paid_amount) >= flt(self.total) and self.total:
            self.status = "Paid"

    def on_submit(self):
        for row in self.get("items") or []:
            if row.product and frappe.db.exists("Product", row.product):
                product = frappe.get_doc("Product", row.product)
                product.current_stock = flt(product.current_stock) + flt(row.qty)
                product.save(ignore_permissions=True)
