# Copyright (c) 2026, Galaxy Labs and Contributors

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle, dashboard_api, portal_api, procurement_api


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


    def test_workspace_sales_views(self):
        client = business_cycle.create_client_record({"business_name": "Workspace Sales Views Client"})
        product = business_cycle.create_product_record({"product_name": "Workspace Quotation Service", "product_type": "Service", "selling_price": 300, "vat_rate": 15})

        quotation = business_cycle.create_frontend_workspace_record("Sales Quotation", {
            "client": client["name"],
            "item": product["name"],
            "qty": 1,
            "rate": 300,
            "vat_rate": 15,
        }, view_key="sales_quotations")
        payment_invoice = business_cycle.create_frontend_workspace_record("Sales Invoice", {
            "client": client["name"],
            "item": product["name"],
            "qty": 1,
            "rate": 300,
            "vat_rate": 15,
        }, view_key="sales_invoices")
        payment = business_cycle.create_frontend_workspace_record("Invoice Payment", {
            "sales_invoice": payment_invoice["name"],
            "amount": 345,
            "payment_method": "Bank Transfer",
        }, view_key="invoice_payments")
        credit_note = business_cycle.create_frontend_workspace_record("Sales Invoice", {
            "client": client["name"],
            "item": product["name"],
            "qty": 1,
            "rate": 100,
            "vat_rate": 15,
        }, view_key="credit_notes")

        quotations = business_cycle.get_frontend_workspace("Sales Quotation", search=quotation["name"], limit=10, view_key="sales_quotations")
        payments = business_cycle.get_frontend_workspace("Invoice Payment", limit=10, view_key="invoice_payments")
        credit_notes = business_cycle.get_frontend_workspace("Sales Invoice", limit=10, view_key="credit_notes")

        self.assertTrue(any(row["name"] == quotation["name"] for row in quotations["records"]))
        self.assertTrue(any(row["name"] == payment["name"] for row in payments["records"]))
        self.assertTrue(any(row["name"] == credit_note["name"] for row in credit_notes["records"]))


    def test_workspace_clients_module_views(self):
        client = business_cycle.create_client_record({
            "business_name": "Client Module Demo",
            "first_name": "Client Module Demo",
            "phone": "+966500001111",
        })
        contact = business_cycle.create_frontend_workspace_record("Client Contact", {
            "client": client["name"],
            "contact_name": "Alaa Contact",
            "email": "alaa@example.com",
            "is_primary": 1,
        })
        appointment = business_cycle.create_frontend_workspace_record("Appointment", {
            "client": client["name"],
            "appointment_date": "2026-06-24",
            "status": "Scheduled",
        })
        deal = business_cycle.create_frontend_workspace_record("CRM Deal", {
            "client": client["name"],
            "deal_name": "AMC Renewal",
            "stage": "Proposal",
            "expected_value": 12000,
            "probability": 70,
        })

        contacts = business_cycle.get_frontend_workspace("Client Contact", search="Alaa Contact", limit=10)
        appointments = business_cycle.get_frontend_workspace("Appointment", limit=10)
        deals = business_cycle.get_frontend_workspace("CRM Deal", search="AMC Renewal", limit=10)

        self.assertTrue(any(row["name"] == contact["name"] for row in contacts["records"]))
        self.assertTrue(any(row["name"] == appointment["name"] for row in appointments["records"]))
        self.assertTrue(any(row["name"] == deal["name"] for row in deals["records"]))

    def test_workspace_credit_views(self):
        client = business_cycle.create_client_record({
            "business_name": "Credit Demo Client",
            "first_name": "Credit Demo Client",
            "phone": "+966500001112",
        })
        credit_type = business_cycle.create_frontend_workspace_record("Credit Type", {
            "type_name": "Visit Credits",
            "unit_label": "Visits",
            "default_credits": 5,
            "active": 1,
        })
        credit_package = business_cycle.create_frontend_workspace_record("Credit Package", {
            "package_name": "Visit Pack 10",
            "credit_type": credit_type["name"],
            "credits": 10,
            "price": 1000,
            "active": 1,
        })
        charge = business_cycle.create_frontend_workspace_record("Credit Charge", {
            "client": client["name"],
            "credit_type": credit_type["name"],
            "credit_package": credit_package["name"],
            "amount": 10,
        })
        usage = business_cycle.create_frontend_workspace_record("Credit Usage", {
            "client": client["name"],
            "credit_type": credit_type["name"],
            "credit_package": credit_package["name"],
            "amount": 3,
        })

        charges = business_cycle.get_frontend_workspace("Credit Charge", limit=10)
        usages = business_cycle.get_frontend_workspace("Credit Usage", limit=10)

        self.assertTrue(any(row["name"] == charge["name"] for row in charges["records"]))
        self.assertTrue(any(row["name"] == usage["name"] for row in usages["records"]))


    def test_run_service_cycle_creates_operational_records(self):
        client = business_cycle.create_client_record({
            "business_name": "Service Cycle Client",
            "first_name": "Service Cycle Client",
            "phone": "+966500001113",
        })
        product = business_cycle.create_product_record({
            "product_name": "Switchgear Relocation Service",
            "product_type": "Service",
            "selling_price": 800,
            "purchase_price": 500,
            "vat_rate": 15,
            "description": "Relocation of switchgear panels",
        })
        employee = frappe.new_doc("Employee")
        employee.employee_name = "Service Engineer"
        employee.employee_id = "EMP-SVC-001"
        employee.email = "service.engineer@example.com"
        employee.hire_date = "2026-01-01"
        employee.basic_salary = 6000
        employee.insert(ignore_permissions=True)

        result = business_cycle.run_service_cycle(payload={
            "client": client["name"],
            "product": product["name"],
            "item": product["name"],
            "employee": employee.name,
            "create_project": 1,
            "project_name": "Sakaka Substation Relocation",
            "budget_amount": 100000,
            "booking_date": "2026-06-24",
            "booking_time": "10:00:00",
            "duration_hours": 4,
            "hourly_rate": 800,
            "cost_rate": 500,
            "qty": 1,
            "rate": 800,
            "vat_rate": 15,
            "invoice_layout": "Materials & Services",
            "description_of_work": "Relocation of Trip and Close Block of 13.8 kV Switchgear Panels at Al Tuwair Substation SAKAKA.",
            "task": "Panel relocation and testing",
        })

        self.assertTrue(result["appointment"]["name"])
        self.assertTrue(result["booking"]["name"])
        self.assertTrue(result["project"]["name"])
        self.assertTrue(result["time_entry"]["name"])
        self.assertTrue(result["invoice"]["name"])
        self.assertEqual(result["invoice"]["project"], result["project"]["name"])
        self.assertTrue(result["profitability"]["cost_center"])


    def test_workspace_inventory_views(self):
        warehouse = business_cycle.create_frontend_workspace_record("Warehouse", {
            "warehouse_name": "Inventory Demo Warehouse",
            "location": "Riyadh",
            "status": "Active",
        })
        price_list = business_cycle.create_frontend_workspace_record("Price List", {
            "price_list_name": "Inventory Demo Price List",
            "currency": "SAR",
            "is_default": 0,
        })
        product = business_cycle.create_product_record({
            "product_name": "Inventory Demo Product",
            "product_type": "Product",
            "selling_price": 50,
            "purchase_price": 30,
            "vat_rate": 15,
        })
        rule = business_cycle.create_frontend_workspace_record("Price List Rule", {
            "product": product["name"],
            "price_list": price_list["name"],
            "rate": 55,
            "min_qty": 1,
        })
        requisition = business_cycle.create_frontend_workspace_record("Requisition", {
            "request_date": "2026-06-24",
            "warehouse": warehouse["name"],
            "status": "Open",
            "purpose": "Service spare parts",
        })

        warehouses = business_cycle.get_frontend_workspace("Warehouse", search="Inventory Demo Warehouse", limit=10)
        rules = business_cycle.get_frontend_workspace("Price List Rule", limit=10)
        requisitions = business_cycle.get_frontend_workspace("Requisition", limit=10)

        self.assertTrue(any(row["name"] == warehouse["name"] for row in warehouses["records"]))
        self.assertTrue(any(row["name"] == rule["name"] for row in rules["records"]))
        self.assertTrue(any(row["name"] == requisition["name"] for row in requisitions["records"]))

    def test_workspace_stock_entry_updates_product_stock(self):
        warehouse = business_cycle.create_frontend_workspace_record("Warehouse", {
            "warehouse_name": "Stock Flow Warehouse",
            "location": "Jeddah",
            "status": "Active",
        })
        product = business_cycle.create_product_record({
            "product_name": "Stock Flow Product",
            "product_type": "Product",
            "selling_price": 20,
            "purchase_price": 10,
            "current_stock": 0,
            "vat_rate": 15,
        })
        created = business_cycle.create_frontend_workspace_record("Stock Entry", {
            "entry_type": "Stock Receipt",
            "date": "2026-06-24",
            "warehouse": warehouse["name"],
            "product": product["name"],
            "qty": 5,
            "rate": 10,
        })
        product_doc = frappe.get_doc("Product", product["name"])

        self.assertTrue(created["name"])
        self.assertEqual(product_doc.current_stock, 5)


    def test_workspace_purchase_reference_flow(self):
        supplier = business_cycle.create_frontend_workspace_record("Supplier", {
            "supplier_name": "Reference Supplier",
            "email": "supplier.ref@example.com",
        })
        product = business_cycle.create_product_record({
            "product_name": "Reference Product",
            "product_type": "Product",
            "selling_price": 100,
            "purchase_price": 70,
            "vat_rate": 15,
        })
        sales_quotation = business_cycle.create_frontend_workspace_record("Sales Quotation", {
            "client": business_cycle.create_client_record({"business_name": "Ref Client", "first_name": "Ref Client", "phone": "+966500001114"})["name"],
            "item": product["name"],
            "qty": 1,
            "rate": 100,
            "vat_rate": 15,
        }, view_key="sales_quotations")
        purchase_quotation = business_cycle.create_frontend_workspace_record("Purchase Quotation", {
            "supplier": supplier["name"],
            "product": product["name"],
            "qty": 2,
            "rate": 70,
            "sales_quotation_reference": sales_quotation["name"],
            "supplier_quotation_no": "SUP-Q-001",
            "customer_purchase_order_no": "CPO-001",
            "proforma_invoice_reference": "PRO-001",
        })
        purchase_order = business_cycle.create_frontend_workspace_record("Purchase Order", {
            "source_purchase_quotation": purchase_quotation["name"],
            "sales_quotation_reference": sales_quotation["name"],
            "supplier_quotation_no": "SUP-Q-001",
            "customer_purchase_order_no": "CPO-001",
            "proforma_invoice_reference": "PRO-001",
            "notes": "Created from quotation",
        })
        purchase_invoice = business_cycle.create_frontend_workspace_record("Purchase Invoice", {
            "source_purchase_order": purchase_order["name"],
            "sales_quotation_reference": sales_quotation["name"],
            "supplier_invoice_no": "SUP-INV-001",
            "customer_purchase_order_no": "CPO-001",
            "proforma_invoice_reference": "PRO-001",
        })

        order_detail = business_cycle.get_frontend_record("Purchase Order", purchase_order["name"])
        invoice_detail = business_cycle.get_frontend_record("Purchase Invoice", purchase_invoice["name"])

        self.assertEqual(order_detail["sales_quotation_reference"], sales_quotation["name"])
        self.assertEqual(order_detail["supplier_quotation_no"], "SUP-Q-001")
        self.assertEqual(invoice_detail["source_purchase_order"], purchase_order["name"])
        self.assertEqual(invoice_detail["supplier_invoice_no"], "SUP-INV-001")

    def test_copy_procurement_document_draft_and_portal_documents(self):
        supplier = business_cycle.create_frontend_workspace_record("Supplier", {
            "supplier_name": "Portal Supplier",
            "email": "portal.supplier@example.com",
        })
        client = business_cycle.create_client_record({
            "business_name": "Portal Client",
            "first_name": "Portal Client",
            "email": "portal.client@example.com",
            "phone": "+966500001115",
        })
        product = business_cycle.create_product_record({
            "product_name": "Portal Product",
            "product_type": "Product",
            "selling_price": 110,
            "purchase_price": 80,
            "vat_rate": 15,
        })
        sales_quotation = business_cycle.create_frontend_workspace_record("Sales Quotation", {
            "client": client["name"],
            "item": product["name"],
            "qty": 1,
            "rate": 110,
            "vat_rate": 15,
        }, view_key="sales_quotations")
        copied_name = procurement_api.copy_procurement_document_draft("Sales Quotation", sales_quotation["name"], "Purchase Quotation", supplier=supplier["name"])
        portal_user = portal_api.create_party_portal_user("Client", client["name"], email="portal.client@example.com")
        supplier_portal_user = portal_api.create_party_portal_user("Supplier", supplier["name"], email="portal.supplier@example.com")
        client_docs = portal_api.get_party_portal_documents("Client", client["name"])
        supplier_docs = portal_api.get_party_portal_documents("Supplier", supplier["name"])

        self.assertTrue(copied_name)
        self.assertEqual(portal_user["party_name"], client["name"])
        self.assertEqual(supplier_portal_user["party_name"], supplier["name"])
        self.assertIn("quotations", client_docs)
        self.assertIn("quotations", supplier_docs)
