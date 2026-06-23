import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class Product(Document):
    def validate(self):
        if not self.product_code:
            frappe.throw(_("Product code is required"))
        if not self.product_name:
            frappe.throw(_("Product name is required"))
        self.selling_price = flt(self.selling_price)
        self.purchase_price = flt(self.purchase_price)
        self.wholesale_price = flt(self.wholesale_price)
        self.vat_rate = flt(self.vat_rate)
        if self.selling_price < 0 or self.purchase_price < 0 or self.wholesale_price < 0:
            frappe.throw(_("Prices cannot be negative"))
        if self.vat_rate < 0:
            frappe.throw(_("VAT rate cannot be negative"))
        if self.product_type == "Service":
            self.unit_of_measure = self.unit_of_measure or "SVC"
            self.opening_stock = 0
            self.current_stock = 0
            self.minimum_stock = 0
            self.maximum_stock = 0
