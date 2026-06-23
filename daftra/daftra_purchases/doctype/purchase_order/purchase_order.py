import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class PurchaseOrder(Document):
    def validate(self):
        if not self.supplier:
            frappe.throw(_("Supplier is required"))
        if not self.order_date:
            self.order_date = nowdate()
        if self.expected_delivery and getdate(self.expected_delivery) < getdate(self.order_date):
            frappe.throw(_("Expected delivery cannot be before order date"))
        if not self.get("items"):
            frappe.throw(_("At least one item is required"))

        subtotal = 0
        tax_amount = 0
        for row in self.items:
            row.qty = flt(row.qty)
            row.rate = flt(row.rate) or flt(frappe.db.get_value("Product", row.product, "purchase_price") or 0)
            if row.qty <= 0:
                frappe.throw(_("Item quantity must be greater than zero"))
            if row.product and not row.description:
                row.description = frappe.db.get_value("Product", row.product, "description") or frappe.db.get_value("Product", row.product, "product_name") or row.product
            if row.product and not row.vat_rate:
                row.vat_rate = frappe.db.get_value("Product", row.product, "vat_rate") or 0
            row.amount = row.qty * row.rate
            row.vat_amount = row.amount * flt(row.vat_rate) / 100
            subtotal += row.amount
            tax_amount += row.vat_amount

        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total = subtotal + tax_amount
        if not self.currency:
            self.currency = "SAR"
        if self.docstatus == 1:
            self.status = "Submitted"
        elif not self.status:
            self.status = "Draft"

    def on_cancel(self):
        self.db_set("status", "Cancelled", update_modified=False)
