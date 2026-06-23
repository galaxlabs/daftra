import frappe
from frappe import _
from frappe.model.document import Document

from daftra.api.project_api import sync_project_cost_center


class Expense(Document):
    def validate(self):
        if not self.expense_date:
            frappe.throw(_("Expense date is required"))
        sync_project_cost_center(self)
