import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from daftra.api.credit_api import apply_credit_defaults, get_client_credit_balance


class CreditUsage(Document):
    def validate(self):
        apply_credit_defaults(self)
        available_balance = get_client_credit_balance(
            self.client,
            self.credit_type,
            exclude_usage=self.name if not self.is_new() else None,
        )
        if flt(self.amount) > flt(available_balance):
            frappe.throw(
                _("Insufficient credit balance. Available balance is {0}.").format(available_balance)
            )
