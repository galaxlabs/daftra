import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, now_datetime


class POSSession(Document):
    def validate(self):
        if not self.user:
            self.user = frappe.session.user
        if not self.opening_time:
            self.opening_time = now_datetime()
        if self.closing_time and get_datetime(self.closing_time) < get_datetime(self.opening_time):
            frappe.throw(_("Closing time cannot be before opening time"))
        self.opening_balance = flt(self.opening_balance)
        self.closing_balance = flt(self.closing_balance)
        self.total_sales = flt(self.total_sales)
        if self.opening_balance < 0 or self.closing_balance < 0:
            frappe.throw(_("POS balances cannot be negative"))

        if self.status == "Closed" or self.closing_time:
            self.total_sales = self._compute_total_sales()
            if not self.closing_time:
                self.closing_time = now_datetime()
            if not self.closing_balance:
                self.closing_balance = self.opening_balance + self.total_sales
            self.status = "Closed"
        elif not self.status:
            self.status = "Open"

    def _compute_total_sales(self):
        start = get_datetime(self.opening_time).date()
        end = get_datetime(self.closing_time or now_datetime()).date()
        return flt(frappe.db.sql(
            """
            SELECT COALESCE(SUM(total), 0)
            FROM `tabSales Invoice`
            WHERE docstatus = 1
              AND sales_person = %s
              AND invoice_date BETWEEN %s AND %s
            """,
            (self.user, start, end),
        )[0][0] or 0)
