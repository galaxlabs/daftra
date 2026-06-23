import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CostCenter(Document):
    def validate(self):
        if not self.cost_center_name:
            frappe.throw(_("Cost center name is required"))
        if self.parent_cost_center and self.parent_cost_center == self.name:
            frappe.throw(_("Cost center cannot be its own parent"))
        if flt(self.budget_amount) < 0:
            frappe.throw(_("Budget cannot be negative"))
