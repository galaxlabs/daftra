import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class InstallmentAgreement(Document):
    def validate(self):
        self.total_amount = flt(self.total_amount)
        self.down_payment = flt(self.down_payment)
        self.number_of_installments = int(self.number_of_installments or 0)

        if not self.client:
            frappe.throw(_('Client is required'))
        if self.total_amount <= 0:
            frappe.throw(_('Total Amount must be greater than zero'))
        if self.down_payment < 0:
            frappe.throw(_('Down Payment cannot be negative'))
        if self.down_payment > self.total_amount:
            frappe.throw(_('Down Payment cannot exceed Total Amount'))
        if self.number_of_installments <= 0:
            frappe.throw(_('Number of Installments must be greater than zero'))

        remaining = self.total_amount - self.down_payment
        self.installment_amount = remaining / self.number_of_installments
        self.status = self.status or 'Active'
