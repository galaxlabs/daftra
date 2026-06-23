import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate

from daftra.api.project_api import sync_project_cost_center


class MaintenanceOrder(Document):
    def validate(self):
        if not self.client:
            frappe.throw(_('Client is required'))
        self.request_date = self.request_date or nowdate()
        self.status = self.status or 'Draft'
        if self.assigned_to and self.status == 'Draft':
            self.status = 'Assigned'
        sync_project_cost_center(self)
