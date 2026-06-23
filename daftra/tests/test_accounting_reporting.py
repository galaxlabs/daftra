# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import accounting_api, business_cycle


class TestAccountingReporting(FrappeTestCase):
    def test_profit_loss_and_balance_sheet_include_operational_documents(self):
        asset = frappe.new_doc("Account")
        asset.account_name = "Bank Cash"
        asset.account_number = "1010"
        asset.account_type = "Asset"
        asset.balance = 1500
        asset.insert(ignore_permissions=True)

        equity = frappe.new_doc("Account")
        equity.account_name = "Owner Equity"
        equity.account_number = "3010"
        equity.account_type = "Equity"
        equity.balance = -1500
        equity.insert(ignore_permissions=True)

        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "Reporting Client",
            "first_name": "Reporting Client",
        })
        supplier = business_cycle._demo_supplier()
        product = business_cycle.create_service_product({
            "product_code": "RPT-001",
            "product_name": "Reporting Service",
            "selling_price": 200,
            "purchase_price": 80,
            "vat_rate": 15,
        })

        sales_invoice = frappe.new_doc("Sales Invoice")
        sales_invoice.client = client["name"]
        sales_invoice.invoice_date = "2026-01-05"
        sales_invoice.due_date = "2026-01-31"
        sales_invoice.append("items", {"item": product["name"], "qty": 2, "rate": 200, "vat_rate": 15})
        sales_invoice.insert(ignore_permissions=True)
        sales_invoice.submit()

        purchase_invoice = frappe.new_doc("Purchase Invoice")
        purchase_invoice.supplier = supplier.name
        purchase_invoice.invoice_date = "2026-01-06"
        purchase_invoice.append("items", {"product": product["name"], "qty": 1, "rate": 80, "vat_rate": 15})
        purchase_invoice.insert(ignore_permissions=True)
        purchase_invoice.submit()

        income = frappe.new_doc("Income")
        income.income_date = "2026-01-07"
        income.amount = 50
        income.insert(ignore_permissions=True)

        expense = frappe.new_doc("Expense")
        expense.expense_date = "2026-01-08"
        expense.amount = 25
        expense.insert(ignore_permissions=True)

        pnl = accounting_api.get_profit_loss("2026-01-01", "2026-01-31")
        balance_sheet = accounting_api.get_balance_sheet("2026-01-31")
        trial_balance = accounting_api.get_trial_balance("2026-01-31")

        self.assertEqual(round(pnl["income"]["sales_invoices"], 2), 460.0)
        self.assertEqual(round(pnl["income"]["direct_income"], 2), 50.0)
        self.assertEqual(round(pnl["expenses"]["purchase_invoices"], 2), 92.0)
        self.assertEqual(round(pnl["expenses"]["direct_expenses"], 2), 25.0)
        self.assertEqual(round(pnl["net_profit"], 2), 393.0)

        self.assertEqual(round(balance_sheet["totals"]["assets"], 2), 1500.0)
        self.assertEqual(round(balance_sheet["totals"]["equity"], 2), -1500.0)
        self.assertGreater(balance_sheet["receivables"], 0)
        self.assertGreater(balance_sheet["payables"], 0)

        self.assertEqual(round(trial_balance["total_debit"], 2), 1500.0)
        self.assertEqual(round(trial_balance["total_credit"], 2), 1500.0)

    def test_recent_activity_returns_sorted_documents(self):
        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "Activity Client",
            "first_name": "Activity Client",
        })
        product = business_cycle.create_service_product({
            "product_code": "ACT-001",
            "product_name": "Activity Service",
            "selling_price": 100,
            "vat_rate": 15,
        })

        invoice = frappe.new_doc("Sales Invoice")
        invoice.client = client["name"]
        invoice.invoice_date = "2026-02-01"
        invoice.due_date = "2026-02-10"
        invoice.append("items", {"item": product["name"], "qty": 1, "rate": 100, "vat_rate": 15})
        invoice.insert(ignore_permissions=True)

        activity = accounting_api.get_recent_activity(5)
        self.assertTrue(activity)
        self.assertIn("doctype", activity[0])
