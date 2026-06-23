import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class Stocktaking(Document):
    def validate(self):
        if not self.warehouse:
            frappe.throw(_("Warehouse is required"))
        if not self.date:
            self.date = nowdate()
        if not self.status:
            self.status = "Draft"

    def on_submit(self):
        self.db_set("status", "Completed", update_modified=False)

    def on_cancel(self):
        self.db_set("status", "Cancelled", update_modified=False)
