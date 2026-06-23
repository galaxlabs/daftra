import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class Employee(Document):
    def validate(self):
        if not self.employee_name:
            frappe.throw(_("Employee name is required"))
        if self.email and "@" not in self.email:
            frappe.throw(_("A valid email address is required"))
        if flt(self.basic_salary) < 0:
            frappe.throw(_("Basic salary cannot be negative"))
        if self.hire_date and getdate(self.hire_date) > getdate(nowdate()):
            frappe.throw(_("Hire date cannot be in the future"))
        if not self.type:
            self.type = "Full Time"
        if not self.status:
            self.status = "Active"
