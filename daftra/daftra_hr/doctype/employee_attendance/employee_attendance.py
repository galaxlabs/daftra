import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time


def _seconds(value):
    parsed = get_time(value)
    return parsed.hour * 3600 + parsed.minute * 60 + parsed.second


class EmployeeAttendance(Document):
    def validate(self):
        if not self.employee:
            frappe.throw(_("Employee is required"))
        if not self.attendance_date:
            frappe.throw(_("Attendance date is required"))
        if self.check_in and self.check_out and _seconds(self.check_out) < _seconds(self.check_in):
            frappe.throw(_("Check out cannot be before check in"))

        if self.shift and self.check_in and self.status not in {"Holiday", "Absent", "Half Day"}:
            shift = frappe.get_doc("Shift", self.shift)
            late = _seconds(self.check_in) > (_seconds(shift.start_time) + int(shift.late_grace_period or 0) * 60)
            self.status = "Late" if late else "Present"
        elif self.check_in and not self.status:
            self.status = "Present"
        elif not self.status:
            self.status = "Absent"
