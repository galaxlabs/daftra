import frappe
from frappe import _
from frappe.utils import add_days, add_months, flt, getdate, nowdate


REFERENCE_PREFIX_RECURRING = 'Recurring Invoice: '
REFERENCE_PREFIX_INSTALLMENT = 'Installment Agreement: '
DEFAULT_SERVICE_PRODUCT_CODE = 'DFT-SVC-AUTO'


def _series_for(doctype):
    meta = frappe.get_meta(doctype)
    field = meta.get_field('naming_series')
    if field and field.options:
        return field.options.splitlines()[0]
    return None


def _prepare_series(doc):
    if doc.meta.has_field('naming_series') and not getattr(doc, 'naming_series', None):
        doc.naming_series = _series_for(doc.doctype)


def _save(doc, submit=False):
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    if submit and getattr(doc.meta, 'is_submittable', 0) and getattr(doc, 'docstatus', 0) == 0:
        doc.submit()
    return doc


def _ensure_service_product():
    existing = frappe.db.get_value('Product', {'product_code': DEFAULT_SERVICE_PRODUCT_CODE}, 'name')
    if existing:
        return existing

    doc = frappe.new_doc('Product')
    doc.product_code = DEFAULT_SERVICE_PRODUCT_CODE
    doc.product_name = 'Automated Service Charge'
    doc.category = 'Services'
    doc.brand = 'Daftra'
    doc.product_type = 'Service'
    doc.unit_of_measure = 'SVC'
    doc.purchase_price = 0
    doc.selling_price = 0
    doc.current_stock = 0
    doc.minimum_stock = 0
    doc.vat_rate = 15
    doc.status = 'Active'
    doc.description = 'System generated service line'
    _prepare_series(doc)
    return _save(doc).name


def _advance_date(date_value, frequency):
    base = getdate(date_value)
    if frequency == 'Daily':
        return add_days(base, 1)
    if frequency == 'Weekly':
        return add_days(base, 7)
    if frequency == 'Monthly':
        return add_months(base, 1)
    if frequency == 'Quarterly':
        return add_months(base, 3)
    if frequency == 'Yearly':
        return add_months(base, 12)
    return base


def _generated_invoice_count(reference_prefix, reference_name):
    return frappe.db.count('Sales Invoice', {'notes': ['like', f'%{reference_prefix}{reference_name}%']})


def _create_invoice(client, amount, invoice_type, note_reference, posting_date=None, sales_person=None, description=None):
    posting_date = posting_date or nowdate()
    product_name = _ensure_service_product()
    invoice = frappe.new_doc('Sales Invoice')
    invoice.client = client
    invoice.invoice_date = posting_date
    credit_period = frappe.db.get_value('Client', client, 'credit_period') or 30
    invoice.due_date = add_days(posting_date, credit_period)
    invoice.currency = frappe.db.get_single_value('Daftra Settings', 'default_currency') or 'SAR'
    invoice.invoice_type = invoice_type
    invoice.sales_person = sales_person
    invoice.notes = f'{note_reference}{description or ""}'.strip()
    invoice.append('items', {
        'item': product_name,
        'description': description or note_reference.strip(),
        'qty': 1,
        'rate': flt(amount),
        'vat_rate': 15,
    })
    _prepare_series(invoice)
    return _save(invoice, submit=True)


@frappe.whitelist()
def create_invoice_from_recurring(recurring_name, posting_date=None):
    recurring = frappe.get_doc('Recurring Invoice', recurring_name)
    if recurring.status not in {'Active', 'Paused'}:
        frappe.throw(_('Only active recurring invoices can generate invoices'))
    if recurring.status == 'Paused':
        frappe.throw(_('Recurring invoice is paused'))

    invoice = _create_invoice(
        recurring.client,
        recurring.total_amount,
        'Recurring',
        f'{REFERENCE_PREFIX_RECURRING}{recurring.name}',
        posting_date or recurring.next_invoice_date or recurring.start_date,
        getattr(recurring, 'sales_person', None),
        f'Recurring billing for {recurring.client}',
    )
    current_date = posting_date or recurring.next_invoice_date or recurring.start_date
    next_date = _advance_date(current_date, recurring.frequency)
    recurring.next_invoice_date = next_date
    if recurring.end_date and getdate(next_date) > getdate(recurring.end_date):
        recurring.status = 'Completed'
    recurring.save(ignore_permissions=True)
    return invoice.name


@frappe.whitelist()
def process_due_recurring_invoices(run_date=None):
    run_date = getdate(run_date or nowdate())
    names = frappe.get_all(
        'Recurring Invoice',
        filters={'status': 'Active', 'next_invoice_date': ['<=', run_date]},
        pluck='name',
    )
    created = []
    for name in names:
        recurring = frappe.get_doc('Recurring Invoice', name)
        if recurring.end_date and getdate(recurring.end_date) < run_date:
            recurring.db_set('status', 'Completed')
            continue
        created.append(create_invoice_from_recurring(name, str(recurring.next_invoice_date)))
    return created


@frappe.whitelist()
def create_invoice_from_installment(agreement_name, posting_date=None):
    agreement = frappe.get_doc('Installment Agreement', agreement_name)
    if agreement.status not in {'Active', 'Completed'}:
        frappe.throw(_('Only active installment agreements can generate invoices'))

    generated = _generated_invoice_count(REFERENCE_PREFIX_INSTALLMENT, agreement.name)
    total_installments = int(agreement.number_of_installments or 0)
    if generated >= total_installments:
        agreement.db_set('status', 'Completed')
        frappe.throw(_('All installments have already been generated'))

    invoice = _create_invoice(
        agreement.client,
        agreement.installment_amount,
        'Normal',
        f'{REFERENCE_PREFIX_INSTALLMENT}{agreement.name}',
        posting_date or nowdate(),
        getattr(agreement, 'sales_person', None),
        f'Installment {generated + 1} of {total_installments}',
    )
    generated += 1
    agreement.db_set('status', 'Completed' if generated >= total_installments else 'Active')
    return invoice.name


def _invoice_profit(invoice):
    profit = flt(invoice.total)
    for item in invoice.get('items') or []:
        purchase_price = frappe.db.get_value('Product', item.item, 'purchase_price') if item.item else 0
        profit -= flt(purchase_price) * flt(item.qty)
    return max(profit, 0)


def _select_commission_rule(invoice):
    if not invoice.sales_person:
        return None
    rules = frappe.get_all(
        'Commission Rule',
        filters={'enabled': 1},
        fields=['name', 'sales_person', 'basis', 'commission_rate', 'starts_on', 'ends_on'],
        order_by='commission_rate desc, modified desc',
    )
    invoice_date = getdate(invoice.invoice_date or nowdate())
    for rule in rules:
        if rule.sales_person and rule.sales_person != invoice.sales_person:
            continue
        if rule.starts_on and getdate(rule.starts_on) > invoice_date:
            continue
        if rule.ends_on and getdate(rule.ends_on) < invoice_date:
            continue
        basis = rule.basis or 'Invoice Total'
        if basis == 'Service Type' and not getattr(invoice, 'type_of_service', None):
            continue
        if basis == 'Product' and not (invoice.get('items') or []):
            continue
        return rule
    return None


def apply_commission_for_invoice(invoice, method=None):
    if isinstance(invoice, str):
        invoice = frappe.get_doc('Sales Invoice', invoice)
    if not invoice.sales_person:
        return None
    existing = frappe.db.get_value('Sales Commission', {'invoice': invoice.name, 'sales_person': invoice.sales_person}, 'name')
    if existing:
        return existing

    rule = _select_commission_rule(invoice)
    if not rule:
        return None

    base_amount = _invoice_profit(invoice) if rule.basis == 'Profit' else flt(invoice.total)
    amount = base_amount * flt(rule.commission_rate) / 100
    if amount <= 0:
        return None

    commission = frappe.new_doc('Sales Commission')
    commission.sales_person = invoice.sales_person
    commission.invoice = invoice.name
    commission.commission_rate = rule.commission_rate
    commission.commission_amount = amount
    commission.status = 'Pending'
    _prepare_series(commission)
    return _save(commission).name


def cancel_commission_for_invoice(invoice, method=None):
    invoice_name = invoice if isinstance(invoice, str) else invoice.name
    for name in frappe.get_all('Sales Commission', filters={'invoice': invoice_name}, pluck='name'):
        frappe.db.set_value('Sales Commission', name, 'status', 'Cancelled', update_modified=True)
