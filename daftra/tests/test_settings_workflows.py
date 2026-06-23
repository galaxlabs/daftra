# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api.dashboard_api import save_frontend_setup


class TestSettingsWorkflows(FrappeTestCase):
    def test_frontend_setup_normalizes_language_code(self):
        state = save_frontend_setup({
            "company_name": "Galaxy Labs",
            "business_type": "Services",
            "default_language": "ar",
            "default_currency": "SAR",
        })

        settings = frappe.get_single("Daftra Settings")
        self.assertEqual(settings.default_language, "Arabic")
        self.assertEqual(state["default_language"], "Arabic")

    def test_zatca_requires_company_and_vat_number(self):
        settings = frappe.get_single("Daftra Settings")
        settings.company_name = ""
        settings.vat_number = ""
        settings.enable_zatca = 1

        with self.assertRaises(frappe.ValidationError):
            settings.save(ignore_permissions=True)
