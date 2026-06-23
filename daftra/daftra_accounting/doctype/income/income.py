import frappe
from frappe import _
from frappe.model.document import Document

from daftra.api.project_api import sync_project_cost_center


class Income(Document):
    def validate(self):
        if not self.income_date:
            frappe.throw(_("Income date is required"))
        sync_project_cost_center(self)
