import frappe
from frappe import _
from frappe.model.document import Document


class Warehouse(Document):
    def validate(self):
        if not self.warehouse_name:
            frappe.throw(_("Warehouse name is required"))
        if not self.status:
            self.status = "Active"
        if self.is_default:
            frappe.db.sql(
                """
                UPDATE `tabWarehouse`
                SET is_default = 0
                WHERE name != %s
                """,
                self.name or "",
            )
