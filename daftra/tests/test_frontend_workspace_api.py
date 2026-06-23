# Copyright (c) 2026, Galaxy Labs and Contributors

from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle, dashboard_api


class TestFrontendWorkspaceAPI(FrappeTestCase):
    def test_setup_state_exposes_industries(self):
        setup = dashboard_api.get_setup_state()
        self.assertIn("business_industries", setup)
        self.assertIn("industry_options", setup)
        self.assertTrue(setup["industry_options"])

    def test_workspace_create_and_list_client(self):
        created = business_cycle.create_frontend_workspace_record("Client", {
            "business_name": "Workspace Demo Client",
            "email": "workspace.client@example.com",
            "phone": "+966500000999",
        })
        workspace = business_cycle.get_frontend_workspace("Client", search="Workspace Demo Client", limit=10)
        self.assertEqual(workspace["doctype"], "Client")
        self.assertTrue(any(row["name"] == created["name"] for row in workspace["records"]))

    def test_workspace_create_invoice(self):
        client = business_cycle.create_client_record({"business_name": "Workspace Invoice Client", "first_name": "Workspace Invoice Client"})
        product = business_cycle.create_product_record({"product_name": "Workspace Service", "product_type": "Service", "selling_price": 500, "vat_rate": 15})
        created = business_cycle.create_frontend_workspace_record("Sales Invoice", {
            "client": client["name"],
            "item": product["name"],
            "qty": 2,
            "rate": 500,
            "vat_rate": 15,
            "description_of_work": "Detailed relocation service package",
            "invoice_layout": "Materials & Services",
        })
        detail = business_cycle.get_frontend_record("Sales Invoice", created["name"])
        self.assertEqual(detail["client"], client["name"])
        self.assertEqual(len(detail["items"]), 1)
