import frappe
from frappe import _
from frappe.model.document import Document


class RequestType(Document):
    def validate(self):
        if not self.request_name:
            frappe.throw(_("Request name is required"))
        if not self.category:
            self.category = "General"
        if self.active is None:
            self.active = 1
