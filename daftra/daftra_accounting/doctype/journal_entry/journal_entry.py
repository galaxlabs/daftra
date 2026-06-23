import frappe
from frappe import _
from frappe.model.document import Document

from daftra.api.project_api import sync_project_cost_center


class JournalEntry(Document):
    def validate(self):
        if not self.posting_date:
            frappe.throw(_("Posting date is required"))
        sync_project_cost_center(self)
