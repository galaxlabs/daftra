import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate, nowdate

from daftra.api.project_api import sync_project_cost_center


def _update_stock(rows, multiplier=1):
    for row in rows:
        if row.product:
            current_stock = flt(frappe.db.get_value("Product", row.product, "current_stock") or 0)
            frappe.db.set_value("Product", row.product, "current_stock", current_stock + (flt(row.qty) * multiplier), update_modified=False)


class PurchaseInvoice(Document):
    def validate(self):
        if not self.invoice_date:
            self.invoice_date = nowdate()
        if self.payment_terms_days and not self.due_date:
            self.due_date = add_days(self.invoice_date, self.payment_terms_days)
        if self.due_date and getdate(self.due_date) < getdate(self.invoice_date):
            frappe.throw(_("Due Date cannot be before Invoice Date"))
        if not self.get("items"):
            frappe.throw(_("At least one item is required"))

        subtotal = 0
        tax_amount = 0
        for row in self.get("items") or []:
            row.qty = flt(row.qty)
            row.rate = flt(row.rate) or flt(frappe.db.get_value("Product", row.product, "purchase_price") or 0)
            if row.qty <= 0:
                frappe.throw(_("Item quantity must be greater than zero"))
            if row.product and not row.description:
                row.description = frappe.db.get_value("Product", row.product, "description") or frappe.db.get_value("Product", row.product, "product_name") or row.product
            if row.product and not row.vat_rate:
                row.vat_rate = frappe.db.get_value("Product", row.product, "vat_rate") or 0
            row.amount = row.qty * row.rate
            row.vat_amount = row.amount * flt(getattr(row, "vat_rate", 0)) / 100
            subtotal += row.amount
            tax_amount += row.vat_amount

        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total = subtotal + tax_amount
        self.balance = self.total - flt(self.paid_amount)
        if self.balance <= 0 and self.total:
            self.status = "Paid"
        elif self.docstatus == 1:
            self.status = "Submitted"
        elif not self.status:
            self.status = "Draft"
        if not self.invoice_type:
            self.invoice_type = "Purchase"
        sync_project_cost_center(self)

    def on_submit(self):
        _update_stock(self.items, multiplier=1)

    def on_cancel(self):
        _update_stock(self.items, multiplier=-1)
