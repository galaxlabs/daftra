# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle
from daftra.api.sales_workflow_api import (
    apply_commission_for_invoice,
    create_invoice_from_installment,
    process_due_recurring_invoices,
)


class TestSalesWorkflows(FrappeTestCase):
    def test_process_due_recurring_invoice_creates_invoice_and_advances_date(self):
        client = business_cycle.create_client_record({
            'client_type': 'Business',
            'business_name': 'Recurring Client',
            'first_name': 'Recurring Client',
        })
        recurring = frappe.new_doc('Recurring Invoice')
        recurring.client = client['name']
        recurring.frequency = 'Monthly'
        recurring.start_date = '2026-01-01'
        recurring.next_invoice_date = '2026-01-01'
        recurring.total_amount = 500
        recurring.status = 'Active'
        recurring.insert(ignore_permissions=True)

        created = process_due_recurring_invoices('2026-01-01')
        recurring.reload()

        self.assertEqual(len(created), 1)
        self.assertEqual(str(recurring.next_invoice_date), '2026-02-01')

    def test_installment_invoice_generation_marks_completion(self):
        client = business_cycle.create_client_record({
            'client_type': 'Business',
            'business_name': 'Installment Client',
            'first_name': 'Installment Client',
        })
        agreement = frappe.new_doc('Installment Agreement')
        agreement.client = client['name']
        agreement.total_amount = 1000
        agreement.down_payment = 100
        agreement.number_of_installments = 3
        agreement.insert(ignore_permissions=True)

        invoices = [
            create_invoice_from_installment(agreement.name, '2026-01-01'),
            create_invoice_from_installment(agreement.name, '2026-02-01'),
            create_invoice_from_installment(agreement.name, '2026-03-01'),
        ]
        agreement.reload()

        self.assertEqual(len(invoices), 3)
        self.assertEqual(agreement.status, 'Completed')
        self.assertEqual(round(agreement.installment_amount, 2), 300.00)

    def test_sales_invoice_submit_creates_commission(self):
        client = business_cycle.create_client_record({
            'client_type': 'Business',
            'business_name': 'Commission Client',
            'first_name': 'Commission Client',
        })
        product = business_cycle.create_service_product({
            'product_code': 'COM-SVC-001',
            'product_name': 'Commission Service',
            'selling_price': 1000,
            'purchase_price': 400,
            'vat_rate': 15,
        })
        rule = frappe.new_doc('Commission Rule')
        rule.rule_name = 'Default Sales Rule'
        rule.sales_person = 'Administrator'
        rule.basis = 'Invoice Total'
        rule.commission_rate = 10
        rule.insert(ignore_permissions=True)

        invoice = frappe.new_doc('Sales Invoice')
        invoice.client = client['name']
        invoice.sales_person = 'Administrator'
        invoice.invoice_date = '2026-01-01'
        invoice.due_date = '2026-01-31'
        invoice.append('items', {'item': product['name'], 'description': 'Commission service', 'qty': 1, 'rate': 1000, 'vat_rate': 15})
        invoice.insert(ignore_permissions=True)
        invoice.submit()

        commission_name = frappe.db.get_value('Sales Commission', {'invoice': invoice.name, 'sales_person': 'Administrator'}, 'name')
        self.assertTrue(commission_name)
        commission = frappe.get_doc('Sales Commission', commission_name)
        self.assertGreater(commission.commission_amount, 0)

    def test_maintenance_order_syncs_project_cost_center(self):
        client = business_cycle.create_client_record({
            'client_type': 'Business',
            'business_name': 'Maintenance Client',
            'first_name': 'Maintenance Client',
        })
        from daftra.api.project_api import create_project_record
        project = create_project_record({
            'project_code': 'MNT-001',
            'project_name': 'Maintenance Project',
            'client_name': client['name'],
        })
        order = frappe.new_doc('Maintenance Order')
        order.client = client['name']
        order.project = project['name']
        order.request_date = '2026-01-01'
        order.assigned_to = 'Administrator'
        order.problem_description = 'Inspection required'
        order.insert(ignore_permissions=True)

        self.assertEqual(order.cost_center, project['cost_center'])
        self.assertEqual(order.status, 'Assigned')
