# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle


class TestHRPOSWorkflows(FrappeTestCase):
    def test_contract_updates_employee_and_payroll_computes_net_salary(self):
        role = frappe.new_doc("Employee Role")
        role.role_name = "Technician"
        role.insert(ignore_permissions=True)

        employee = frappe.new_doc("Employee")
        employee.employee_name = "Ahmad Technician"
        employee.role = role.name
        employee.hire_date = "2026-01-01"
        employee.insert(ignore_permissions=True)

        contract = frappe.new_doc("Employee Contract")
        contract.employee = employee.name
        contract.start_date = "2026-01-01"
        contract.basic_salary = 5000
        contract.insert(ignore_permissions=True)

        employee.reload()
        self.assertEqual(employee.basic_salary, 5000)
        self.assertEqual(employee.status, "Active")

        payroll = frappe.new_doc("Payroll Entry")
        payroll.employee = employee.name
        payroll.payroll_month = "Jan"
        payroll.payroll_year = 2026
        payroll.allowances = 500
        payroll.deductions = 250
        payroll.insert(ignore_permissions=True)

        self.assertEqual(payroll.basic_salary, 5000)
        self.assertEqual(payroll.net_salary, 5250)

    def test_attendance_and_leave_request_calculations(self):
        employee = frappe.new_doc("Employee")
        employee.employee_name = "Mona Clerk"
        employee.hire_date = "2026-01-01"
        employee.insert(ignore_permissions=True)

        shift = frappe.new_doc("Shift")
        shift.shift_name = "Morning"
        shift.start_time = "08:00:00"
        shift.end_time = "16:00:00"
        shift.late_grace_period = 15
        shift.insert(ignore_permissions=True)

        attendance = frappe.new_doc("Employee Attendance")
        attendance.employee = employee.name
        attendance.attendance_date = "2026-01-10"
        attendance.shift = shift.name
        attendance.check_in = "08:20:00"
        attendance.insert(ignore_permissions=True)

        leave = frappe.new_doc("Leave Request")
        leave.employee = employee.name
        leave.from_date = "2026-01-15"
        leave.to_date = "2026-01-17"
        leave.insert(ignore_permissions=True)

        self.assertEqual(attendance.status, "Late")
        self.assertEqual(leave.total_days, 3)

    def test_pos_session_closes_with_sales_total(self):
        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "POS Client",
            "first_name": "POS Client",
        })
        product = business_cycle.create_service_product({
            "product_code": "POS-SVC-001",
            "product_name": "POS Service",
            "selling_price": 100,
            "vat_rate": 15,
        })

        invoice = frappe.new_doc("Sales Invoice")
        invoice.client = client["name"]
        invoice.sales_person = "Administrator"
        invoice.invoice_date = "2026-01-05"
        invoice.due_date = "2026-01-06"
        invoice.append("items", {"item": product["name"], "qty": 2, "rate": 100, "vat_rate": 15})
        invoice.insert(ignore_permissions=True)
        invoice.submit()

        session = frappe.new_doc("POS Session")
        session.user = "Administrator"
        session.opening_time = "2026-01-05 08:00:00"
        session.closing_time = "2026-01-05 22:00:00"
        session.opening_balance = 1000
        session.insert(ignore_permissions=True)

        self.assertEqual(session.total_sales, 230)
        self.assertEqual(session.closing_balance, 1230)
        self.assertEqual(session.status, "Closed")
