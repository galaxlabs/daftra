import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SalesInvoiceItem(Document):
    def validate(self):
        self.qty = flt(self.qty)
        self.rate = flt(self.rate)
        self.vat_rate = flt(self.vat_rate)
        if self.qty <= 0:
            frappe.throw(_("Quantity must be greater than zero"))
        if self.rate < 0:
            frappe.throw(_("Rate cannot be negative"))
        if self.item and not self.description:
            self.description = frappe.db.get_value("Product", self.item, "description") or frappe.db.get_value("Product", self.item, "product_name") or self.item
        if self.item and not self.rate:
            self.rate = flt(frappe.db.get_value("Product", self.item, "selling_price") or 0)
        if self.item and not self.vat_rate:
            self.vat_rate = flt(frappe.db.get_value("Product", self.item, "vat_rate") or 0)
        self.amount = self.qty * self.rate
        self.vat_amount = self.amount * self.vat_rate / 100
