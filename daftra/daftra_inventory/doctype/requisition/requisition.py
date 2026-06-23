import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class Requisition(Document):
    def validate(self):
        if not self.request_date:
            self.request_date = nowdate()
        if not self.requested_by:
            self.requested_by = frappe.session.user
        if self.needed_by and getdate(self.needed_by) < getdate(self.request_date):
            frappe.throw(_("Needed by date cannot be before request date"))
        if not self.status:
            self.status = "Open"
