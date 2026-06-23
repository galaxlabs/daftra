import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate, nowdate


class PurchaseQuotation(Document):
    def validate(self):
        if not self.quotation_date:
            self.quotation_date = nowdate()
        if not self.valid_till:
            self.valid_till = add_days(self.quotation_date, 7)
        if self.valid_till and getdate(self.valid_till) < getdate(self.quotation_date):
            frappe.throw(_("Valid till date cannot be before quotation date"))

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
            row.vat_amount = row.amount * flt(row.vat_rate) / 100
            subtotal += row.amount
            tax_amount += row.vat_amount

        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total = subtotal + tax_amount
        if not getattr(self, "currency", None):
            self.currency = "SAR"
        if not self.status:
            self.status = "Sent" if self.supplier else "Draft"
