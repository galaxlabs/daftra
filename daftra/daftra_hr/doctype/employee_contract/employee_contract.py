import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class EmployeeContract(Document):
    def validate(self):
        if not self.employee:
            frappe.throw(_("Employee is required"))
        if not self.start_date:
            frappe.throw(_("Start date is required"))
        if self.end_date and self.end_date < self.start_date:
            frappe.throw(_("End date cannot be before start date"))
        if flt(self.basic_salary) < 0:
            frappe.throw(_("Basic salary cannot be negative"))
        if not self.contract_type:
            self.contract_type = "Permanent"
        if not self.basic_salary:
            self.basic_salary = flt(frappe.db.get_value("Employee", self.employee, "basic_salary") or 0)
        if self.status == "Terminated":
            return
        if self.end_date and self.end_date < nowdate():
            self.status = "Expired"
        else:
            self.status = "Active"

    def on_update(self):
        employee = frappe.get_doc("Employee", self.employee)
        employee.basic_salary = self.basic_salary
        if self.status == "Terminated":
            employee.status = "Terminated"
        elif employee.status != "Suspended":
            employee.status = "Active"
        employee.save(ignore_permissions=True)
