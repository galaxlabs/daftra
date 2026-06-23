import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PriceListRule(Document):
    def validate(self):
        if not self.product:
            frappe.throw(_("Product is required"))
        if not self.price_list:
            frappe.throw(_("Price list is required"))
        self.rate = flt(self.rate)
        self.min_qty = flt(self.min_qty)
        self.max_qty = flt(self.max_qty)
        if self.rate < 0:
            frappe.throw(_("Rate cannot be negative"))
        if self.min_qty < 0 or self.max_qty < 0:
            frappe.throw(_("Quantity limits cannot be negative"))
        if self.max_qty and self.max_qty < self.min_qty:
            frappe.throw(_("Max quantity cannot be less than min quantity"))

    def on_update(self):
        default_list = frappe.db.get_value("Price List", {"is_default": 1}, "name")
        if self.price_list == default_list and self.min_qty <= 1 and not self.max_qty:
            frappe.db.set_value("Product", self.product, "selling_price", self.rate, update_modified=False)
