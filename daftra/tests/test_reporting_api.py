# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle, reporting_api


class TestReportingAPI(FrappeTestCase):
    def test_reports_catalog_contains_daftra_groups(self):
        catalog = reporting_api.get_reports_catalog()
        self.assertIn("invoices", catalog)
        self.assertIn("accounting", catalog)
        self.assertIn("inventory", catalog)
        self.assertIn("time_tracking", catalog)

    def test_sales_purchase_clients_and_credits_reports(self):
        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "Report API Client",
            "first_name": "Report API Client",
        })
        supplier = business_cycle._demo_supplier()
        product = business_cycle.create_service_product({
            "product_code": "REP-API-001",
            "product_name": "Report API Service",
            "selling_price": 120,
            "purchase_price": 60,
            "vat_rate": 15,
        })

        sinv = frappe.new_doc("Sales Invoice")
        sinv.client = client["name"]
        sinv.invoice_date = "2026-03-01"
        sinv.due_date = "2026-03-31"
        sinv.append("items", {"item": product["name"], "qty": 1, "rate": 120, "vat_rate": 15})
        sinv.insert(ignore_permissions=True)
        sinv.submit()

        pinv = frappe.new_doc("Purchase Invoice")
        pinv.supplier = supplier.name
        pinv.invoice_date = "2026-03-02"
        pinv.append("items", {"product": product["name"], "qty": 1, "rate": 60, "vat_rate": 15})
        pinv.insert(ignore_permissions=True)
        pinv.submit()

        ctype = frappe.new_doc("Credit Type")
        ctype.type_name = "Visits"
        ctype.insert(ignore_permissions=True)
        charge = frappe.new_doc("Credit Charge")
        charge.client = client["name"]
        charge.credit_type = ctype.name
        charge.amount = 10
        charge.insert(ignore_permissions=True)

        sales = reporting_api.get_sales_report("2026-03-01", "2026-03-31")
        purchases = reporting_api.get_purchase_report("2026-03-01", "2026-03-31")
        clients = reporting_api.get_clients_report()
        credits = reporting_api.get_credits_report()

        self.assertGreaterEqual(round(sales["total_sales"], 2), 138.0)
        self.assertGreaterEqual(round(purchases["total_purchases"], 2), 69.0)
        self.assertGreaterEqual(clients["total_clients"], 1)
        self.assertGreaterEqual(round(credits["charged"], 2), 10.0)

    def test_inventory_time_tracking_and_pos_reports(self):
        warehouse = frappe.new_doc("Warehouse")
        warehouse.warehouse_name = "Reports Warehouse"
        warehouse.insert(ignore_permissions=True)

        product = frappe.new_doc("Product")
        product.product_code = "RPT-INV-001"
        product.product_name = "Inventory Report Product"
        product.product_type = "Product"
        product.selling_price = 50
        product.current_stock = 2
        product.minimum_stock = 5
        product.insert(ignore_permissions=True)

        entry = frappe.new_doc("Time Entry")
        entry.employee = ""
        entry.task = "Reporting Task"
        entry.date = "2026-03-10"
        entry.start_time = "09:00:00"
        entry.end_time = "11:00:00"
        entry.duration_hours = 2
        entry.billable_amount = 300
        entry.cost_amount = 100
        entry.insert(ignore_permissions=True)

        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "POS Report Client",
            "first_name": "POS Report Client",
        })
        pos_product = business_cycle.create_service_product({
            "product_code": "RPT-POS-001",
            "product_name": "POS Report Service",
            "selling_price": 200,
            "vat_rate": 15,
        })
        invoice = frappe.new_doc("Sales Invoice")
        invoice.client = client["name"]
        invoice.sales_person = "Administrator"
        invoice.invoice_date = "2026-03-10"
        invoice.due_date = "2026-03-11"
        invoice.append("items", {"item": pos_product["name"], "qty": 1, "rate": 200, "vat_rate": 15})
        invoice.insert(ignore_permissions=True)
        invoice.submit()

        pos = frappe.new_doc("POS Session")
        pos.user = "Administrator"
        pos.opening_time = "2026-03-10 08:00:00"
        pos.closing_time = "2026-03-10 16:00:00"
        pos.opening_balance = 500
        pos.status = "Closed"
        pos.insert(ignore_permissions=True)

        inventory = reporting_api.get_inventory_report()
        timing = reporting_api.get_time_tracking_report("2026-03-01", "2026-03-31")
        pos_report = reporting_api.get_pos_report("2026-03-01", "2026-03-31")

        self.assertGreaterEqual(inventory["total_products"], 1)
        self.assertTrue(any(row["product_code"] == "RPT-INV-001" for row in inventory["low_stock"]))
        self.assertEqual(round(timing["total_hours"], 2), 2.0)
        self.assertEqual(round(pos_report["total_sales"], 2), 230.0)
