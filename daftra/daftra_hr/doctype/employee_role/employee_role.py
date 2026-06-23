import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeRole(Document):
    def validate(self):
        if not self.role_name:
            frappe.throw(_("Role name is required"))
        if self.is_admin and not self.permissions:
            self.permissions = "all"
