import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class Appointment(Document):
    def validate(self):
        if not self.client:
            frappe.throw(_("Client is required"))
        if not self.appointment_date:
            self.appointment_date = nowdate()
        if not self.status:
            self.status = "Scheduled"
