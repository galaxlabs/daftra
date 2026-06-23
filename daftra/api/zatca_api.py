import base64
import json
from datetime import datetime

import frappe
from frappe import _
from frappe.utils import flt


def _tlv_tag(tag, value):
    payload = value.encode('utf-8')
    return bytes([tag, len(payload)]) + payload


def _invoice_timestamp(invoice):
    invoice_date = getattr(invoice, 'invoice_date', None)
    if invoice_date:
        return f"{invoice_date}T00:00:00Z"
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


@frappe.whitelist()
def get_zatca_qr(invoice_name):
    """Generate ZATCA QR code data for an invoice"""
    invoice = frappe.get_doc('Sales Invoice', invoice_name)
    settings = frappe.get_single('Daftra Settings')

    if not settings.enable_zatca:
        frappe.throw(_('ZATCA is not enabled in settings'))

    qr_fields = [
        (1, settings.company_name or ''),
        (2, settings.vat_number or ''),
        (3, _invoice_timestamp(invoice)),
        (4, f"{flt(invoice.total or 0):.2f}"),
        (5, f"{flt(invoice.tax_amount or 0):.2f}"),
    ]
    tlv = b''.join(_tlv_tag(tag, value) for tag, value in qr_fields)
    qr_base64 = base64.b64encode(tlv).decode('ascii')
    checks = validate_zatca_invoice(invoice_name)
    return {
        'seller_name': settings.company_name or '',
        'vat_number': settings.vat_number or '',
        'timestamp': _invoice_timestamp(invoice),
        'total': float(invoice.total or 0),
        'vat_total': float(invoice.tax_amount or 0),
        'tlv': qr_base64,
        'compliance': checks,
    }


@frappe.whitelist()
def validate_zatca_invoice(invoice_name):
    invoice = frappe.get_doc('Sales Invoice', invoice_name)
    settings = frappe.get_single('Daftra Settings')
    errors = []
    warnings = []

    if not settings.company_name:
        errors.append(_('Company name is required'))
    if not settings.vat_number:
        errors.append(_('VAT number is required'))
    if not getattr(invoice, 'client', None):
        errors.append(_('Client is required'))
    client = frappe.get_doc('Client', invoice.client) if getattr(invoice, 'client', None) else None
    if client and client.client_type == 'Business' and not client.tax_id:
        warnings.append(_('Business client does not have a VAT / Tax ID'))
    if flt(invoice.total or 0) <= 0:
        errors.append(_('Invoice total must be greater than zero'))
    if flt(invoice.tax_amount or 0) < 0:
        errors.append(_('Tax amount cannot be negative'))
    if getattr(invoice, 'invoice_layout', '') == 'TAX Invoice' and not getattr(invoice, 'invoice_date', None):
        errors.append(_('Invoice date is required for TAX Invoice'))

    return {'ok': not errors, 'errors': errors, 'warnings': warnings}
