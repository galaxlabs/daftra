from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document


class Shift(Document):
    def validate(self):
        if not self.shift_name:
            frappe.throw(_("Shift name is required"))
        if not self.start_time or not self.end_time:
            frappe.throw(_("Start time and end time are required"))
        if (self.late_grace_period or 0) < 0:
            frappe.throw(_("Late grace period cannot be negative"))
        start = datetime.strptime(str(self.start_time), "%H:%M:%S")
        end = datetime.strptime(str(self.end_time), "%H:%M:%S")
        if start == end:
            frappe.throw(_("Shift start and end time cannot be the same"))
