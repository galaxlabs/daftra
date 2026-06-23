# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle


class TestBusinessCycle(FrappeTestCase):
    def test_create_service_product_applies_service_defaults(self):
        product = business_cycle.create_service_product({
            "product_code": "TST-SVC-001",
            "product_name": "Test Service Package",
            "selling_price": 150,
            "vat_rate": 15,
        })

        self.assertEqual(product["product_type"], "Service")
        self.assertEqual(product["unit_of_measure"], "SVC")
        self.assertEqual(product["current_stock"], 0)
        self.assertEqual(product["selling_price"], 150)
        self.assertEqual(product["vat_rate"], 15)

    def test_run_service_cycle_returns_service_documents(self):
        result = business_cycle.run_service_cycle()

        self.assertIn("booking", result)
        self.assertIn("time_entry", result)
        self.assertIn("invoice", result)
        self.assertIn("payment", result)
        self.assertGreater(result["total"], 0)

    def test_project_scope_sets_service_invoice_defaults(self):
        doc = frappe.new_doc("Sales Invoice")
        doc.client = self._create_client_name()
        doc.project_title = "Relocation of Trip and Close Block of 13.8 kV Switchgear Panels"
        doc.project_reference = "ATU-SAK-0138"
        doc.project_location = "Al Tuwair Substation, Sakaka"
        doc.project_scope = "Relocation of Trip and Close Block of 13.8 kV Switchgear Panels at Al Tuwair Substation Sakaka."
        doc.contract_acknowledgement = "CONTRACTOR'S ACKNOWLEDGEMENT"
        doc.append("items", {"item": self._create_service_product_name(), "qty": 1, "rate": 100})
        doc.validate()

        self.assertEqual(doc.invoice_layout, "Materials & Services")
        self.assertEqual(doc.type_of_service, "Maintenance")
        self.assertIn("Al Tuwair", doc.description_of_work)

    def _create_client_name(self):
        from daftra.api.business_cycle import create_client_record
        return create_client_record({"client_type": "Business", "business_name": "Project Demo Client", "first_name": "Project Demo Client"})["name"]

    def _create_service_product_name(self):
        from daftra.api.business_cycle import create_service_product
        return create_service_product({"product_code": "TST-SVC-PROJ", "product_name": "Project Service", "selling_price": 100, "vat_rate": 15})["name"]

