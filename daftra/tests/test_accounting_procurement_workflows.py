# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle
from daftra.api.procurement_api import (
    create_purchase_invoice_from_order,
    create_purchase_order_from_quotation,
    create_purchase_quotation_from_request,
)


class TestAccountingProcurementWorkflows(FrappeTestCase):
    def test_journal_entry_balances_accounts_on_submit_and_cancel(self):
        cash = frappe.new_doc("Account")
        cash.account_name = "Cash In Hand"
        cash.account_number = "1001"
        cash.account_type = "Asset"
        cash.insert(ignore_permissions=True)

        revenue = frappe.new_doc("Account")
        revenue.account_name = "Service Revenue"
        revenue.account_number = "4001"
        revenue.account_type = "Revenue"
        revenue.insert(ignore_permissions=True)

        entry = frappe.new_doc("Journal Entry")
        entry.posting_date = "2026-01-01"
        entry.append("accounts", {"account": cash.name, "debit": 1000})
        entry.append("accounts", {"account": revenue.name, "credit": 1000})
        entry.insert(ignore_permissions=True)
        entry.submit()

        cash.reload()
        revenue.reload()
        self.assertEqual(entry.total_debit, 1000)
        self.assertEqual(entry.total_credit, 1000)
        self.assertEqual(cash.balance, 1000)
        self.assertEqual(revenue.balance, -1000)

        entry.cancel()
        cash.reload()
        revenue.reload()
        self.assertEqual(cash.balance, 0)
        self.assertEqual(revenue.balance, 0)

    def test_purchase_invoice_updates_stock_on_submit(self):
        supplier_doc = business_cycle._demo_supplier()
        product = frappe.new_doc("Product")
        product.product_code = "PROC-001"
        product.product_name = "Procurement Item"
        product.product_type = "Product"
        product.purchase_price = 50
        product.selling_price = 80
        product.current_stock = 3
        product.vat_rate = 15
        product.insert(ignore_permissions=True)

        invoice = frappe.new_doc("Purchase Invoice")
        invoice.supplier = supplier_doc.name
        invoice.invoice_date = "2026-01-01"
        invoice.append("items", {"product": product.name, "qty": 4, "rate": 50})
        invoice.insert(ignore_permissions=True)
        invoice.submit()

        updated_stock = frappe.db.get_value("Product", product.name, "current_stock")
        self.assertEqual(invoice.total, 230)
        self.assertEqual(updated_stock, 7)

        invoice.cancel()
        reverted_stock = frappe.db.get_value("Product", product.name, "current_stock")
        self.assertEqual(reverted_stock, 3)

    def test_purchase_order_autofills_totals(self):
        supplier_doc = business_cycle._demo_supplier()
        product = frappe.new_doc("Product")
        product.product_code = "PO-001"
        product.product_name = "PO Item"
        product.product_type = "Product"
        product.purchase_price = 25
        product.selling_price = 40
        product.vat_rate = 5
        product.insert(ignore_permissions=True)

        order = frappe.new_doc("Purchase Order")
        order.supplier = supplier_doc.name
        order.order_date = "2026-01-01"
        order.append("items", {"product": product.name, "qty": 2})
        order.insert(ignore_permissions=True)

        self.assertEqual(order.subtotal, 50)
        self.assertEqual(order.tax_amount, 2.5)
        self.assertEqual(order.total, 52.5)


    def test_procurement_conversion_flow_updates_statuses(self):
        supplier_doc = business_cycle._demo_supplier()
        request = frappe.new_doc("Purchase Request")
        request.request_date = "2026-01-01"
        request.insert(ignore_permissions=True)
        request.submit()

        quotation_name = create_purchase_quotation_from_request(request.name, supplier=supplier_doc.name)
        quotation = frappe.get_doc("Purchase Quotation", quotation_name)
        self.assertEqual(quotation.status, "Sent")

        product = frappe.new_doc("Product")
        product.product_code = "FLOW-001"
        product.product_name = "Flow Item"
        product.product_type = "Product"
        product.purchase_price = 60
        product.selling_price = 95
        product.vat_rate = 15
        product.insert(ignore_permissions=True)

        quotation.append("items", {"product": product.name, "qty": 2, "rate": 60})
        quotation.save(ignore_permissions=True)

        order_name = create_purchase_order_from_quotation(quotation.name)
        quotation.reload()
        order = frappe.get_doc("Purchase Order", order_name)
        self.assertEqual(quotation.status, "Accepted")
        self.assertEqual(order.total, 138)

        order.submit()
        invoice_name = create_purchase_invoice_from_order(order.name, submit_invoice=1)
        order.reload()
        invoice = frappe.get_doc("Purchase Invoice", invoice_name)

        self.assertEqual(order.status, "Received")
        self.assertEqual(invoice.total, 138)

    def test_default_warehouse_switches_previous_default_off(self):
        first = frappe.new_doc("Warehouse")
        first.warehouse_name = "Primary Warehouse"
        first.is_default = 1
        first.insert(ignore_permissions=True)

        second = frappe.new_doc("Warehouse")
        second.warehouse_name = "Secondary Warehouse"
        second.is_default = 1
        second.insert(ignore_permissions=True)

        first.reload()
        second.reload()
        self.assertEqual(first.is_default, 0)
        self.assertEqual(second.is_default, 1)
