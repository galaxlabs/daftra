import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class Treasury(Document):
    def validate(self):
        self.treasury_name = (self.treasury_name or '').strip()
        self.account_number = (self.account_number or '').strip()
        self.bank_name = (self.bank_name or '').strip()
        self.iban = (self.iban or '').replace(' ', '').upper()
        self.balance = flt(self.balance)

        if not self.treasury_name:
            frappe.throw(_('Treasury name is required'))

        if self.type == 'Bank Account' and not self.bank_name:
            frappe.throw(_('Bank Name is required for Bank Account treasuries'))

        if self.type == 'Bank Account' and not self.account_number:
            frappe.throw(_('Account Number is required for Bank Account treasuries'))
