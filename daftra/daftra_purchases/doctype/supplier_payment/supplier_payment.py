import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class SupplierPayment(Document):
    def validate(self):
        if not self.payment_date:
            self.payment_date = nowdate()
        if flt(self.amount) <= 0:
            frappe.throw(_('Payment amount must be greater than zero'))
        self._resolve_payment_source()

    def after_insert(self):
        self._apply_payment()

    def on_submit(self):
        self._apply_payment()

    def _resolve_payment_source(self):
        if self.bank_registration:
            bank = frappe.get_doc('Bank Registration', self.bank_registration)
            self.treasury = bank.linked_treasury
        elif self.payment_method in {'Bank Transfer', 'Card'} and not self.treasury:
            default_bank = frappe.db.get_value('Bank Registration', {'is_active': 1, 'is_default': 1}, ['name', 'linked_treasury'], as_dict=True)
            if default_bank:
                self.bank_registration = default_bank.name
                self.treasury = default_bank.linked_treasury

        if self.payment_method in {'Bank Transfer', 'Card'} and not self.bank_registration:
            frappe.throw(_('Select a Bank Registration for bank-based supplier payments'))

        if self.payment_method == 'Cash' and not self.treasury:
            cash_treasury = frappe.db.get_value('Treasury', {'type': 'Cash', 'is_active': 1}, 'name')
            if cash_treasury:
                self.treasury = cash_treasury

    def _apply_payment(self):
        if self.purchase_invoice:
            invoice = frappe.get_doc('Purchase Invoice', self.purchase_invoice)
            paid_amount = flt(invoice.paid_amount) + flt(self.amount)
            frappe.db.set_value('Purchase Invoice', invoice.name, {
                'paid_amount': paid_amount,
                'status': 'Paid' if paid_amount >= flt(invoice.total) else 'Submitted',
            }, update_modified=True)
        if self.treasury and frappe.db.exists('Treasury', self.treasury):
            balance = flt(frappe.db.get_value('Treasury', self.treasury, 'balance')) - flt(self.amount)
            frappe.db.set_value('Treasury', self.treasury, 'balance', balance, update_modified=True)
        if self.bank_registration and frappe.db.exists('Bank Registration', self.bank_registration):
            current = flt(frappe.db.get_value('Bank Registration', self.bank_registration, 'current_balance')) - flt(self.amount)
            frappe.db.set_value('Bank Registration', self.bank_registration, 'current_balance', current, update_modified=True)
