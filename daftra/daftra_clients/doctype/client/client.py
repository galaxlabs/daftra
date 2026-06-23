import frappe
from frappe import _
from frappe.model.document import Document


class Client(Document):
    def validate(self):
        if not self.first_name and not self.business_name:
            frappe.throw(_("Client name is required"))
        if not self.first_name:
            self.first_name = self.business_name
        if self.client_type == "Business" and not self.business_name:
            self.business_name = self.first_name
        if self.credit_limit and self.credit_limit < 0:
            frappe.throw(_("Credit limit cannot be negative"))
        if self.credit_period and self.credit_period < 0:
            frappe.throw(_("Credit period cannot be negative"))
