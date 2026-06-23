# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle, sales_api
from daftra.api.credit_api import get_client_credit_summary


class TestCreditWorkflows(FrappeTestCase):
    def test_credit_package_charge_and_usage_updates_balance(self):
        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "Credit Client",
            "first_name": "Credit Client",
        })

        credit_type = frappe.new_doc("Credit Type")
        credit_type.type_name = "Sessions"
        credit_type.default_credits = 5
        credit_type.insert(ignore_permissions=True)

        package = frappe.new_doc("Credit Package")
        package.package_name = "Starter Sessions"
        package.credit_type = credit_type.name
        package.credits = 25
        package.price = 1000
        package.insert(ignore_permissions=True)

        charge = frappe.new_doc("Credit Charge")
        charge.client = client["name"]
        charge.credit_package = package.name
        charge.insert(ignore_permissions=True)

        usage = frappe.new_doc("Credit Usage")
        usage.client = client["name"]
        usage.credit_type = credit_type.name
        usage.amount = 10
        usage.insert(ignore_permissions=True)

        summary = get_client_credit_summary(client["name"])
        profile = sales_api.get_client_profile(client["name"])

        self.assertEqual(charge.credit_type, credit_type.name)
        self.assertEqual(charge.amount, 25)
        self.assertEqual(summary["balance"], 15)
        self.assertEqual(summary["charged"], 25)
        self.assertEqual(summary["used"], 10)
        self.assertEqual(profile["credit_summary"]["balance"], 15)

    def test_credit_usage_cannot_exceed_available_balance(self):
        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "Overuse Client",
            "first_name": "Overuse Client",
        })

        credit_type = frappe.new_doc("Credit Type")
        credit_type.type_name = "Hours"
        credit_type.default_credits = 8
        credit_type.insert(ignore_permissions=True)

        charge = frappe.new_doc("Credit Charge")
        charge.client = client["name"]
        charge.credit_type = credit_type.name
        charge.amount = 8
        charge.insert(ignore_permissions=True)

        usage = frappe.new_doc("Credit Usage")
        usage.client = client["name"]
        usage.credit_type = credit_type.name
        usage.amount = 10

        with self.assertRaises(frappe.ValidationError):
            usage.insert(ignore_permissions=True)
