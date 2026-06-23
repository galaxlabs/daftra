import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, nowdate

from daftra.api.credit_api import get_client_credit_summary


def _client_outstanding_sql(client_name):
    return frappe.db.sql(
        """
        SELECT COALESCE(SUM(total - COALESCE(paid_amount, 0)), 0)
        FROM `tabSales Invoice`
        WHERE client = %s AND docstatus = 1 AND status != 'Paid'
        """,
        client_name,
    )[0][0]


@frappe.whitelist()
def create_invoice_from_quotation(quotation_name):
    """Convert quotation to invoice"""
    quotation = frappe.get_doc('Sales Quotation', quotation_name)
    invoice = frappe.new_doc('Sales Invoice')
    invoice.client = quotation.client
    invoice.currency = quotation.currency
    invoice.payment_terms_days = quotation.payment_terms_days or invoice.payment_terms_days
    invoice.invoice_layout = quotation.invoice_layout or invoice.invoice_layout
    invoice.delivery_method = quotation.delivery_method or invoice.delivery_method
    invoice.sales_person = quotation.sales_person or invoice.sales_person
    invoice.description_of_work = quotation.description_of_work or invoice.description_of_work
    for item in quotation.items:
        invoice.append('items', {
            'item': item.item,
            'description': item.description,
            'qty': item.qty,
            'rate': item.rate,
            'vat_rate': getattr(item, 'vat_rate', None),
            'amount': item.amount
        })
    invoice.insert(ignore_permissions=True)
    return invoice.name


@frappe.whitelist()
def get_client_outstanding(client_name):
    """Get outstanding balance for a client"""
    return _client_outstanding_sql(client_name)


@frappe.whitelist()
def get_client_profile(client_name):
    client = frappe.get_doc('Client', client_name)
    outstanding = _client_outstanding_sql(client_name) if client else 0
    recent_invoice = (frappe.get_all(
        'Sales Invoice',
        filters={'client': client_name},
        fields=['name', 'invoice_date', 'total', 'status'],
        order_by='modified desc',
        limit_page_length=1,
    ) or [None])[0]
    credit_summary = get_client_credit_summary(client_name)
    return {
        'name': client.name,
        'client_type': client.client_type,
        'display_name': client.business_name or ' '.join(filter(None, [client.first_name, client.last_name])),
        'phone': client.phone,
        'mobile': client.mobile,
        'email': client.email,
        'country': client.country,
        'city': client.city,
        'tax_id': client.tax_id,
        'cr_number': client.cr_number,
        'credit_limit': client.credit_limit,
        'credit_period': client.credit_period,
        'outstanding': outstanding,
        'recent_invoice': recent_invoice,
        'credit_summary': credit_summary,
    }


@frappe.whitelist()
def get_product_profile(product_name):
    product = frappe.get_doc('Product', product_name)
    return {
        'name': product.name,
        'product_code': product.product_code,
        'product_name': product.product_name,
        'description': product.description,
        'product_type': product.product_type,
        'unit_of_measure': product.unit_of_measure,
        'selling_price': product.selling_price,
        'purchase_price': product.purchase_price,
        'wholesale_price': product.wholesale_price,
        'vat_rate': product.vat_rate,
        'current_stock': product.current_stock,
        'minimum_stock': product.minimum_stock,
        'status': product.status,
    }


@frappe.whitelist()
def get_sales_workflow_context(client_name=None, product_name=None):
    context = {
        'client': get_client_profile(client_name) if client_name else None,
        'product': get_product_profile(product_name) if product_name else None,
        'today': nowdate(),
    }
    if client_name:
        client = frappe.get_doc('Client', client_name)
        context['due_date'] = add_days(nowdate(), client.credit_period or 30)
    return context


@frappe.whitelist()
def get_workflow_catalog(limit=20):
    limit = int(limit or 20)
    return {
        'clients': frappe.get_all('Client', fields=['name', 'business_name', 'first_name', 'last_name', 'client_type', 'credit_period', 'tax_id'], order_by='modified desc', limit_page_length=limit),
        'products': frappe.get_all('Product', fields=['name', 'product_code', 'product_name', 'product_type', 'selling_price', 'vat_rate', 'current_stock'], order_by='modified desc', limit_page_length=limit),
        'suppliers': frappe.get_all('Supplier', fields=['name', 'supplier_name', 'supplier_type', 'tax_id', 'payment_terms'], order_by='modified desc', limit_page_length=limit),
    }


@frappe.whitelist()
def validate_sales_invoice_payload(payload=None):
    if isinstance(payload, str):
        import json
        payload = json.loads(payload or '{}')
    payload = payload or {}
    errors = []
    settings = frappe.get_single('Daftra Settings')
    client_name = payload.get('client')
    items = payload.get('items') or []
    if not client_name:
        errors.append(_('Client is required'))
    if not items:
        errors.append(_('At least one item is required'))
    if settings.business_type == 'Services' and not payload.get('description_of_work'):
        errors.append(_('Description of work is required in Services mode'))
    if settings.enable_zatca:
        if not settings.company_name:
            errors.append(_('Company name is required for ZATCA'))
        if not settings.vat_number:
            errors.append(_('VAT number is required for ZATCA'))
        if payload.get('invoice_layout') == 'TAX Invoice' and client_name:
            client = frappe.get_doc('Client', client_name)
            if client.client_type == 'Business' and not client.tax_id:
                errors.append(_('Client VAT / Tax ID is required for TAX Invoice'))
    subtotal = 0
    tax_total = 0
    for index, row in enumerate(items, start=1):
        qty = flt(row.get('qty'))
        rate = flt(row.get('rate'))
        vat_rate = flt(row.get('vat_rate') or settings.default_sales_tax or 0)
        if qty <= 0:
            errors.append(_('Row {0}: quantity must be greater than zero').format(index))
        if rate < 0:
            errors.append(_('Row {0}: rate cannot be negative').format(index))
        amount = qty * rate
        subtotal += amount
        tax_total += amount * vat_rate / 100
    total = subtotal - flt(payload.get('discount_amount')) - flt(payload.get('deposit_amount')) + flt(payload.get('adjustment_amount')) + tax_total
    if total <= 0:
        errors.append(_('Invoice total must be greater than zero'))
    return {'ok': not errors, 'errors': errors, 'subtotal': subtotal, 'tax_total': tax_total, 'total': total}
