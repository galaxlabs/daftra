import frappe
from frappe.model.document import Document

from daftra.api.credit_api import apply_credit_defaults


class CreditCharge(Document):
    def validate(self):
        apply_credit_defaults(self)
