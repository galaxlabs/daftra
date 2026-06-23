import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class Account(Document):
    def validate(self):
        if not self.account_name:
            frappe.throw(_("Account name is required"))
        if self.parent_account and self.parent_account == self.name:
            frappe.throw(_("Account cannot be its own parent"))
        if self.account_number and frappe.db.exists("Account", {"account_number": self.account_number, "name": ["!=", self.name or ""]}):
            frappe.throw(_("Account number must be unique"))
        if self.parent_account:
            parent_type = frappe.db.get_value("Account", self.parent_account, "account_type")
            if parent_type and self.account_type and parent_type != self.account_type:
                frappe.throw(_("Parent account must have the same account type"))
        self.balance = flt(self.balance)
