import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class Asset(Document):
    def validate(self):
        if not self.asset_name:
            frappe.throw(_("Asset name is required"))
        if flt(self.purchase_cost) < 0:
            frappe.throw(_("Purchase cost cannot be negative"))
        if self.useful_life_months is not None and self.useful_life_months < 0:
            frappe.throw(_("Useful life cannot be negative"))
        if not self.current_value and flt(self.purchase_cost):
            self.current_value = flt(self.purchase_cost)
        if self.current_value and flt(self.current_value) < 0:
            frappe.throw(_("Current value cannot be negative"))
        if self.depreciation_method == "None":
            self.useful_life_months = 0
        if not self.status:
            self.status = "Active"
