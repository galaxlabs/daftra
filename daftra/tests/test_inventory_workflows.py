# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api.inventory_api import get_product_price


class TestInventoryWorkflows(FrappeTestCase):
    def test_default_price_list_switches_previous_default_off(self):
        first = frappe.new_doc("Price List")
        first.price_list_name = "Retail"
        first.currency = "SAR"
        first.is_default = 1
        first.insert(ignore_permissions=True)

        second = frappe.new_doc("Price List")
        second.price_list_name = "Wholesale"
        second.currency = "SAR"
        second.is_default = 1
        second.insert(ignore_permissions=True)

        first.reload()
        second.reload()
        self.assertEqual(first.is_default, 0)
        self.assertEqual(second.is_default, 1)

    def test_price_rule_resolves_quantity_based_price(self):
        product = frappe.new_doc("Product")
        product.product_code = "PRL-001"
        product.product_name = "Priced Item"
        product.product_type = "Product"
        product.selling_price = 100
        product.insert(ignore_permissions=True)

        price_list = frappe.new_doc("Price List")
        price_list.price_list_name = "Tiered"
        price_list.currency = "SAR"
        price_list.insert(ignore_permissions=True)

        rule = frappe.new_doc("Price List Rule")
        rule.product = product.name
        rule.price_list = price_list.name
        rule.rate = 80
        rule.min_qty = 5
        rule.insert(ignore_permissions=True)

        low_qty = get_product_price(product.name, price_list.name, qty=2)
        bulk_qty = get_product_price(product.name, price_list.name, qty=6)

        self.assertEqual(low_qty["price"], 100)
        self.assertEqual(bulk_qty["price"], 80)

    def test_stocktaking_submit_marks_completed(self):
        warehouse = frappe.new_doc("Warehouse")
        warehouse.warehouse_name = "Count Warehouse"
        warehouse.insert(ignore_permissions=True)

        stocktaking = frappe.new_doc("Stocktaking")
        stocktaking.warehouse = warehouse.name
        stocktaking.date = "2026-01-01"
        stocktaking.insert(ignore_permissions=True)
        stocktaking.submit()

        stocktaking.reload()
        self.assertEqual(stocktaking.status, "Completed")
