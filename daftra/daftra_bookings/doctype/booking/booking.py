import frappe
from frappe import _
from frappe.model.document import Document


class Booking(Document):
    def validate(self):
        if not self.booking_date:
            frappe.throw(_("Booking date is required"))
        if not self.service:
            self.service = "Maintenance"
        if not self.status:
            self.status = "Pending"
