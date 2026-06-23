import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class JournalEntryAccount(Document):
    def validate(self):
        self.debit = flt(self.debit)
        self.credit = flt(self.credit)
        if not self.account:
            frappe.throw(_("Account is required"))
        if self.debit < 0 or self.credit < 0:
            frappe.throw(_("Debit and credit cannot be negative"))
        if not self.debit and not self.credit:
            frappe.throw(_("Either debit or credit is required"))
        if self.debit and self.credit:
            frappe.throw(_("A row cannot have both debit and credit amounts"))
