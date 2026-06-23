import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff


class LeaveRequest(Document):
    def validate(self):
        if not self.employee:
            frappe.throw(_("Employee is required"))
        if not self.from_date or not self.to_date:
            frappe.throw(_("From date and to date are required"))
        if self.to_date < self.from_date:
            frappe.throw(_("To date cannot be before from date"))
        self.total_days = date_diff(self.to_date, self.from_date) + 1
        if not self.leave_type:
            self.leave_type = "Annual"
        if not self.status:
            self.status = "Draft"
