import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class PayrollEntry(Document):
    def validate(self):
        if not self.employee:
            frappe.throw(_("Employee is required"))
        if not self.payroll_year:
            frappe.throw(_("Payroll year is required"))
        if not self.payroll_month:
            self.payroll_month = nowdate()[5:7]
        if not self.basic_salary:
            contract_salary = frappe.db.get_value("Employee Contract", {"employee": self.employee, "status": "Active"}, "basic_salary")
            self.basic_salary = flt(contract_salary or frappe.db.get_value("Employee", self.employee, "basic_salary") or 0)
        self.allowances = flt(self.allowances)
        self.deductions = flt(self.deductions)
        self.basic_salary = flt(self.basic_salary)
        if self.basic_salary < 0 or self.allowances < 0 or self.deductions < 0:
            frappe.throw(_("Payroll amounts cannot be negative"))
        self.net_salary = self.basic_salary + self.allowances - self.deductions
        if self.net_salary < 0:
            frappe.throw(_("Net salary cannot be negative"))
        if not self.status:
            self.status = "Draft"
