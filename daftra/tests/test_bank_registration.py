# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from daftra.api import business_cycle


class TestBankRegistration(FrappeTestCase):
    def test_bank_registration_creates_linked_treasury(self):
        bank = frappe.new_doc('Bank Registration')
        bank.bank_name = 'Saudi National Bank'
        bank.account_title = 'Galaxy Labs Operating'
        bank.account_number = '5000000000001234'
        bank.iban = 'SA0300000000005000000001'
        bank.current_balance = 1000
        bank.insert(ignore_permissions=True)

        self.assertTrue(bank.linked_treasury)
        treasury = frappe.get_doc('Treasury', bank.linked_treasury)
        self.assertEqual(treasury.type, 'Bank Account')
        self.assertEqual(treasury.account_number, bank.account_number)

    def test_invoice_payment_updates_bank_and_invoice_balance(self):
        client = business_cycle.create_client_record({
            'client_type': 'Business',
            'business_name': 'Bank Flow Client',
            'first_name': 'Bank Flow Client',
        })
        product = business_cycle.create_service_product({
            'product_code': 'BANK-SVC-001',
            'product_name': 'Bank Tested Service',
            'selling_price': 200,
            'vat_rate': 15,
        })
        bank = business_cycle._demo_bank_registration()

        invoice = frappe.new_doc('Sales Invoice')
        invoice.client = client['name']
        invoice.invoice_date = '2026-01-01'
        invoice.due_date = '2026-01-31'
        invoice.append('items', {'item': product['name'], 'description': 'Service', 'qty': 1, 'rate': 200, 'vat_rate': 15})
        invoice.insert(ignore_permissions=True)
        invoice.submit()

        before_bank_balance = frappe.db.get_value('Bank Registration', bank.name, 'current_balance')
        payment = frappe.new_doc('Invoice Payment')
        payment.sales_invoice = invoice.name
        payment.payment_date = '2026-01-02'
        payment.amount = invoice.total
        payment.payment_method = 'Bank Transfer'
        payment.bank_registration = bank.name
        payment.insert(ignore_permissions=True)

        invoice.reload()
        updated_bank_balance = frappe.db.get_value('Bank Registration', bank.name, 'current_balance')
        self.assertEqual(invoice.balance, 0)
        self.assertGreater(updated_bank_balance, before_bank_balance)
