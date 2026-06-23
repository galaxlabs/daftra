# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle


class TestClientOperations(FrappeTestCase):
    def test_primary_contact_is_unique_per_client(self):
        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "Contacts Client",
            "first_name": "Contacts Client",
        })

        first = frappe.new_doc("Client Contact")
        first.client = client["name"]
        first.contact_name = "First Contact"
        first.phone = "+966500000010"
        first.is_primary = 1
        first.insert(ignore_permissions=True)

        second = frappe.new_doc("Client Contact")
        second.client = client["name"]
        second.contact_name = "Second Contact"
        second.email = "second@example.com"
        second.is_primary = 1
        second.insert(ignore_permissions=True)

        first.reload()
        second.reload()
        self.assertEqual(first.is_primary, 0)
        self.assertEqual(second.is_primary, 1)

    def test_appointment_and_crm_deal_defaults(self):
        client = business_cycle.create_client_record({
            "client_type": "Business",
            "business_name": "CRM Client",
            "first_name": "CRM Client",
        })

        appointment = frappe.new_doc("Appointment")
        appointment.client = client["name"]
        appointment.appointment_date = "2026-01-01"
        appointment.insert(ignore_permissions=True)

        deal = frappe.new_doc("CRM Deal")
        deal.client = client["name"]
        deal.deal_name = "Annual Service Contract"
        deal.expected_value = 10000
        deal.probability = 60
        deal.insert(ignore_permissions=True)

        self.assertEqual(appointment.status, "Scheduled")
        self.assertEqual(deal.stage, "Lead")
        self.assertEqual(deal.assigned_to, "Administrator")
