
import frappe, json
from frappe import _

@frappe.whitelist()
def get_zatca_qr(invoice_name):
    """Generate ZATCA QR code data for an invoice"""
    invoice = frappe.get_doc('Sales Invoice', invoice_name)
    settings = frappe.get_single('Daftra Settings')
    
    if not settings.enable_zatca:
        frappe.throw(_('ZATCA is not enabled in settings'))
    
    # ZATCA QR requires: seller name, VAT number, timestamp, total, VAT total
    qr_data = {
        'seller_name': settings.company_name or '',
        'vat_number': settings.vat_number or '',
        'timestamp': str(invoice.invoice_date) + 'T00:00:00',
        'total': float(invoice.total or 0),
        'vat_total': float(invoice.tax_amount or 0)
    }
    
    return qr_data
