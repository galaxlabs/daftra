import frappe
from frappe import _
from frappe.model.document import Document

from daftra.api.project_api import ensure_project_cost_center, refresh_project_financials


class DaftraProject(Document):
    def validate(self):
        if not self.project_code:
            frappe.throw(_("Project code is required"))
        if not self.project_name:
            frappe.throw(_("Project name is required"))

    def after_insert(self):
        ensure_project_cost_center(self.name)

    def on_update(self):
        refresh_project_financials(self.name)
