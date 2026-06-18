
import frappe
from frappe import _

@frappe.whitelist()
def create_invoice_from_quotation(quotation_name):
    """Convert quotation to invoice"""
    quotation = frappe.get_doc('Sales Quotation', quotation_name)
    invoice = frappe.new_doc('Sales Invoice')
    invoice.client = quotation.client
    invoice.currency = quotation.currency
    for item in quotation.items:
        invoice.append('items', {
            'item': item.item,
            'description': item.description,
            'qty': item.qty,
            'rate': item.rate,
            'amount': item.amount
        })
    invoice.insert(ignore_permissions=True)
    return invoice.name

@frappe.whitelist()
def get_client_outstanding(client_name):
    """Get outstanding balance for a client"""
    outstanding = frappe.db.sql("""
        SELECT COALESCE(SUM(total - COALESCE(paid_amount, 0)), 0)
        FROM `tabSales Invoice`
        WHERE client = %s AND docstatus = 1 AND status != 'Paid'
    """, client_name)[0][0]
    return outstanding
