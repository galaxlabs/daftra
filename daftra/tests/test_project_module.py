# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle, project_api


class TestProjectModule(FrappeTestCase):
    def test_create_project_auto_creates_cost_center(self):
        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "Project Demo Client",
            "first_name": "Project Demo Client",
        })
        result = project_api.create_project_record({
            "project_code": "PRJ-REL-001",
            "project_name": "Relocation of Trip and Close Block of 13.8 kV Switchgear Panels",
            "client_name": client["name"],
            "budget_amount": 250000,
        })

        self.assertEqual(result["project_code"], "PRJ-REL-001")
        self.assertTrue(result["cost_center"])
        self.assertIn("PRJ-REL-001", result["cost_center_name"])

    def test_project_document_syncs_cost_center_and_profitability(self):
        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "Project Demo Client 2",
            "first_name": "Project Demo Client 2",
        })
        product = business_cycle.create_service_product({
            "product_code": "PRJ-SVC-001",
            "product_name": "Project Service Item",
            "selling_price": 100,
            "vat_rate": 15,
        })
        project = project_api.create_project_record({
            "project_code": "PRJ-REL-002",
            "project_name": "Project Profitability Demo",
            "client_name": client["name"],
            "budget_amount": 100000,
        })

        invoice = frappe.new_doc("Sales Invoice")
        invoice.client = client["name"]
        invoice.project = project["name"]
        invoice.invoice_date = "2026-01-01"
        invoice.due_date = "2026-01-31"
        invoice.append("items", {"item": product["name"], "description": "Project service", "qty": 2, "rate": 100, "vat_rate": 15})
        invoice.insert(ignore_permissions=True)
        invoice.submit()

        expense = frappe.new_doc("Expense")
        expense.expense_date = "2026-01-02"
        expense.amount = 40
        expense.project = project["name"]
        expense.insert(ignore_permissions=True)

        time_entry = frappe.new_doc("Time Entry")
        time_entry.date = "2026-01-03"
        time_entry.duration_hours = 3
        time_entry.hourly_rate = 50
        time_entry.cost_rate = 30
        time_entry.project = project["name"]
        time_entry.insert(ignore_permissions=True)

        summary = project_api.refresh_project_financials(project["name"])
        profitability = project_api.get_project_profitability(project["name"])

        self.assertEqual(invoice.cost_center, project["cost_center"])
        self.assertEqual(expense.cost_center, project["cost_center"])
        self.assertEqual(time_entry.cost_center, project["cost_center"])
        self.assertGreater(summary["revenue"], 0)
        self.assertGreater(summary["cost"], 0)
        self.assertGreater(profitability["revenue"], 0)
        self.assertIn("profit", profitability)
