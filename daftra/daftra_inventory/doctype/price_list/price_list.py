import frappe
from frappe import _
from frappe.model.document import Document


class PriceList(Document):
    def validate(self):
        if not self.price_list_name:
            frappe.throw(_("Price list name is required"))
        if not self.currency:
            self.currency = "SAR"
        if self.is_default:
            frappe.db.sql(
                """
                UPDATE `tabPrice List`
                SET is_default = 0
                WHERE name != %s
                """,
                self.name or "",
            )
