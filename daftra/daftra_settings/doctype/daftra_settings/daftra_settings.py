import frappe
from frappe import _
from frappe.model.document import Document


LANGUAGE_MAP = {
    "en": "English",
    "ar": "Arabic",
    "English": "English",
    "Arabic": "Arabic",
}
BUSINESS_TYPES = {"Services", "Trading", "Retail", "Wholesale", "Mixed"}


class DaftraSettings(Document):
    def validate(self):
        if self.business_type and self.business_type not in BUSINESS_TYPES:
            frappe.throw(_("Unsupported business type"))
        self.default_language = LANGUAGE_MAP.get(self.default_language or "English", "English")
        if not self.default_currency:
            self.default_currency = "SAR"
        if self.enable_zatca:
            if not self.company_name:
                frappe.throw(_("Company name is required when ZATCA is enabled"))
            if not self.vat_number:
                frappe.throw(_("VAT number is required when ZATCA is enabled"))
