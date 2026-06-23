import frappe
from frappe import _
from frappe.model.document import Document


class TaxSetting(Document):
    def validate(self):
        if not self.tax_name:
            frappe.throw(_("Tax name is required"))
        if self.tax_rate is None or self.tax_rate < 0 or self.tax_rate > 100:
            frappe.throw(_("Tax rate must be between 0 and 100"))
        if self.is_zatca_compliant and not self.tax_type:
            self.tax_type = "VAT"
        if self.is_default:
            frappe.db.sql(
                """
                UPDATE `tabTax Setting`
                SET is_default = 0
                WHERE name != %s
                """,
                self.name or "",
            )
