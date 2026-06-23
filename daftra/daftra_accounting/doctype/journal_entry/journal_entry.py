import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from daftra.api.project_api import sync_project_cost_center


def _apply_account_balances(rows, multiplier=1):
    for row in rows:
        account = frappe.get_doc("Account", row.account)
        amount = flt(row.debit) - flt(row.credit)
        account.balance = flt(account.balance) + (amount * multiplier)
        account.save(ignore_permissions=True)


class JournalEntry(Document):
    def validate(self):
        if not self.posting_date:
            frappe.throw(_("Posting date is required"))
        sync_project_cost_center(self)
        if not self.get("accounts"):
            frappe.throw(_("At least one account row is required"))

        total_debit = 0
        total_credit = 0
        for row in self.accounts:
            row.debit = flt(row.debit)
            row.credit = flt(row.credit)
            if not row.cost_center and self.cost_center:
                row.cost_center = self.cost_center
            total_debit += row.debit
            total_credit += row.credit

        self.total_debit = total_debit
        self.total_credit = total_credit
        if round(total_debit, 2) != round(total_credit, 2):
            frappe.throw(_("Total debit must equal total credit"))
        if not self.entry_type:
            self.entry_type = "Journal Entry"

    def on_submit(self):
        _apply_account_balances(self.accounts, multiplier=1)

    def on_cancel(self):
        _apply_account_balances(self.accounts, multiplier=-1)
