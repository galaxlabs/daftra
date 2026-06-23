import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from daftra.api.project_api import sync_project_cost_center


class TimeEntry(Document):
    def validate(self):
        if not self.date:
            frappe.throw(_("Date is required"))
        self.duration_hours = flt(self.duration_hours)
        self.hourly_rate = flt(self.hourly_rate)
        self.cost_rate = flt(getattr(self, "cost_rate", 0) or self.hourly_rate)
        if self.duration_hours and self.duration_hours < 0:
            frappe.throw(_("Duration cannot be negative"))
        if self.hourly_rate < 0:
            frappe.throw(_("Hourly rate cannot be negative"))
        self.billable_amount = flt(self.billable_amount) or self.duration_hours * self.hourly_rate
        self.cost_amount = flt(getattr(self, "cost_amount", 0)) or self.duration_hours * self.cost_rate
        sync_project_cost_center(self)
