import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class BankRegistration(Document):
    def validate(self):
        self.bank_name = (self.bank_name or '').strip()
        self.account_title = (self.account_title or '').strip()
        self.account_number = (self.account_number or '').strip()
        self.iban = (self.iban or '').replace(' ', '').upper()
        self.swift_code = (self.swift_code or '').strip().upper()
        self.branch_name = (self.branch_name or '').strip()
        self.current_balance = flt(self.current_balance or self.opening_balance)

        if not self.bank_name:
            frappe.throw(_('Bank Name is required'))
        if not self.account_title:
            frappe.throw(_('Account Title is required'))
        if not self.account_number:
            frappe.throw(_('Account Number is required'))

        if self.is_default:
            self._unset_other_defaults()

        self._sync_treasury()

    def _unset_other_defaults(self):
        frappe.db.sql(
            """
            update `tabBank Registration`
            set is_default = 0
            where name != %s
            """,
            self.name or '',
        )

    def _sync_treasury(self):
        treasury_name = self.linked_treasury
        if treasury_name and frappe.db.exists('Treasury', treasury_name):
            treasury = frappe.get_doc('Treasury', treasury_name)
        else:
            treasury = frappe.new_doc('Treasury')
            treasury.naming_series = 'TRE-.YYYY.-'

        treasury.treasury_name = f'{self.bank_name} - {self.account_number[-4:]}'
        treasury.type = 'Bank Account'
        treasury.account_number = self.account_number
        treasury.bank_name = self.bank_name
        treasury.iban = self.iban
        treasury.balance = flt(self.current_balance)
        treasury.is_active = self.is_active

        if treasury.is_new():
            treasury.insert(ignore_permissions=True)
        else:
            treasury.save(ignore_permissions=True)

        self.linked_treasury = treasury.name
