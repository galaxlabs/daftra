import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class PurchaseRequest(Document):
    def validate(self):
        if not self.request_date:
            self.request_date = nowdate()
        if not self.requested_by:
            self.requested_by = frappe.session.user
        if not self.status:
            self.status = "Draft"

    def on_submit(self):
        self.db_set("status", "Approved", update_modified=False)

    def on_cancel(self):
        self.db_set("status", "Rejected", update_modified=False)
