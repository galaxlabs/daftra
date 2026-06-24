import html
import json

import frappe
from frappe import _
from frappe.utils import add_days, flt, nowdate

MODULE_MAP = {
    "Sales": ["Sales Invoice", "Sales Quotation", "Invoice Payment", "Recurring Invoice", "Installment Agreement", "Sales Commission"],
    "Clients": ["Client", "Client Contact", "Appointment", "CRM Deal", "Credit Charge", "Credit Usage", "Credit Package", "Credit Type", "Insurance Agent"],
    "Inventory": ["Product", "Warehouse", "Stock Entry", "Stocktaking", "Price List", "Price List Rule", "Requisition"],
    "Purchases": ["Supplier", "Purchase Request", "Purchase Quotation", "Purchase Order", "Purchase Invoice", "Supplier Payment"],
    "Accounting": ["Account", "Cost Center", "Journal Entry", "Expense", "Income", "Treasury", "Bank Registration", "Asset"],
    "HR": ["Employee", "Employee Role", "Shift", "Employee Attendance", "Employee Contract", "Payroll Entry", "Leave Request"],
    "POS": ["POS Session"],
    "Bookings": ["Booking"],
    "Time Tracking": ["Time Entry"],
    "Projects": ["Daftra Project"],
    "Tax": ["Tax Setting"],
    "Settings": ["Daftra Settings"],
}

WORKSPACE_VIEW_ALIASES = {
    "sales_invoices": "Sales Invoice",
    "credit_notes": "Sales Invoice",
    "refund_receipts": "Sales Invoice",
    "sales_quotations": "Sales Quotation",
    "invoice_payments": "Invoice Payment",
    "recurring_invoices": "Recurring Invoice",
}

SCENARIOS = [
    {"key": "lead_to_cash", "label": "Lead to cash", "steps": ["Client", "Quotation", "Invoice", "Payment", "Receipt"]},
    {"key": "procure_to_stock", "label": "Procure to stock", "steps": ["Supplier", "Purchase Invoice", "Stock Increase", "Supplier Payment"]},
    {"key": "service_job", "label": "Service job", "steps": ["Appointment", "Booking", "Project", "Time Entry", "Invoice", "ZATCA QR"]},
    {"key": "hr_payroll", "label": "HR payroll", "steps": ["Employee", "Shift", "Attendance", "Payroll"]},
]

SERIES_FALLBACKS = {
    "Client": "CLI-.YYYY.-",
    "Product": "PRO-.YYYY.-",
    "Supplier": "SUP-.YYYY.-",
    "Sales Invoice": "SAL-.YYYY.-",
    "Sales Quotation": "QUO-.YYYY.-",
    "Invoice Payment": "INV-.YYYY.-",
    "Recurring Invoice": "REC-.YYYY.-",
    "Installment Agreement": "INS-.YYYY.-",
    "Sales Commission": "COM-.YYYY.-",
    "Purchase Request": "PRQ-.YYYY.-",
    "Purchase Quotation": "PQT-.YYYY.-",
    "Purchase Order": "PO-.YYYY.-",
    "Purchase Invoice": "PUR-.YYYY.-",
    "Supplier Payment": "SUP-.YYYY.-",
    "Booking": "BOO-.YYYY.-",
    "Appointment": "APP-.YYYY.-",
    "CRM Deal": "CRM-.YYYY.-",
    "Client Contact": "CLI-.YYYY.-",
    "Credit Charge": "CRE-.YYYY.-",
    "Credit Usage": "CRE-.YYYY.-",
    "Credit Package": "CPK-.YYYY.-",
    "Credit Type": "CTY-.YYYY.-",
    "Insurance Agent": "INS-.YYYY.-",
    "Time Entry": "TIM-.YYYY.-",
    "Daftra Project": "PRJ-.YYYY.-",
    "Employee": "EMP-.YYYY.-",
    "Shift": "SHF-.YYYY.-",
    "Journal Entry": "JRN-.YYYY.-",
    "Expense": "EXP-.YYYY.-",
    "Income": "INC-.YYYY.-",
    "Treasury": "TRE-.YYYY.-",
    "Bank Registration": "BNK-.YYYY.-",
    "Asset": "AST-.YYYY.-",
    "Warehouse": "WAR-.YYYY.-",
    "Price List": "PRI-.YYYY.-",
    "Price List Rule": "PRI-.YYYY.-",
    "Stock Entry": "STO-.YYYY.-",
    "Stocktaking": "STO-.YYYY.-",
    "Requisition": "REQ-.YYYY.-",
    "Supplier": "SUP-.YYYY.-",
}


def _require_manager():
    if "System Manager" not in frappe.get_roles():
        frappe.throw(_("System Manager role is required"), frappe.PermissionError)


def _payload_dict(payload):
    if isinstance(payload, str):
        payload = json.loads(payload or "{}")
    return payload or {}


def _series_for(doctype):
    return SERIES_FALLBACKS.get(doctype) or next(
        (value for value in (frappe.get_meta(doctype).get_field("naming_series").options or "").split("\n") if value),
        None,
    )


def _prepare_series(doc):
    if doc.meta.has_field("naming_series") and not getattr(doc, "naming_series", None):
        doc.naming_series = _series_for(doc.doctype)


def _save(doc, submit=False):
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    if submit and getattr(doc.meta, "is_submittable", 0) and getattr(doc, "docstatus", 0) == 0:
        doc.submit()
    return doc


def _doc_dict(doc, fields=None):
    data = doc.as_dict()
    if fields:
        return {field: data.get(field) for field in fields}
    return data


def _first_or_create(doctype, filters, values):
    name = frappe.db.get_value(doctype, filters, "name")
    if name:
        return frappe.get_doc(doctype, name)
    doc = frappe.new_doc(doctype)
    doc.update(values)
    _prepare_series(doc)
    return _save(doc)


def _demo_client():
    return _first_or_create("Client", {"business_name": "Daftra Demo Trading"}, {
        "client_type": "Business",
        "business_name": "Daftra Demo Trading",
        "first_name": "Daftra Demo",
        "email": "demo.client@example.com",
        "phone": "+966500000001",
        "mobile": "+966500000001",
        "city": "Riyadh",
        "country": "Saudi Arabia",
        "tax_id": "300000000000003",
        "credit_limit": 50000,
        "credit_period": 30,
    })


def _demo_supplier():
    return _first_or_create("Supplier", {"supplier_name": "Daftra Demo Supplier"}, {
        "supplier_name": "Daftra Demo Supplier",
        "supplier_type": "Company",
        "phone": "+966500000002",
        "email": "supplier@example.com",
        "tax_id": "300000000000004",
        "payment_terms": "30 Days",
        "status": "Active",
    })


def _demo_warehouse():
    return _first_or_create("Warehouse", {"warehouse_name": "Main Warehouse"}, {
        "warehouse_name": "Main Warehouse",
        "location": "Riyadh",
        "is_default": 1,
        "status": "Active",
    })


def _demo_bank_registration():
    return _first_or_create("Bank Registration", {"account_number": "4000001234567890"}, {
        "bank_name": "Al Rajhi Bank",
        "account_title": "Galaxy Labs Daftra",
        "account_number": "4000001234567890",
        "iban": "SA0380000000608010167519",
        "swift_code": "RJHISARI",
        "branch_name": "Riyadh Main",
        "currency": "SAR",
        "opening_balance": 150000,
        "current_balance": 150000,
        "is_default": 1,
        "is_active": 1,
    })


def _demo_product():
    return _first_or_create("Product", {"product_code": "DFT-SERVICE-001"}, {
        "product_code": "DFT-SERVICE-001",
        "product_name": "Maintenance Service Package",
        "category": "Services",
        "brand": "Galaxy Labs",
        "product_type": "Service",
        "unit_of_measure": "SVC",
        "purchase_price": 120,
        "selling_price": 250,
        "current_stock": 12,
        "minimum_stock": 5,
        "vat_rate": 15,
        "status": "Active",
    })


def _demo_tax():
    return _first_or_create("Tax Setting", {"tax_name": "VAT 15%"}, {
        "tax_name": "VAT 15%",
        "tax_rate": 15,
        "tax_type": "VAT",
        "is_default": 1,
        "is_zatca_compliant": 1,
        "is_active": 1,
    })


@frappe.whitelist()
def create_client_record(payload=None):
    payload = _payload_dict(payload)
    client = frappe.new_doc("Client")
    client.client_type = payload.get("client_type") or ("Business" if payload.get("business_name") else "Individual")
    client.business_name = payload.get("business_name") or payload.get("company_name") or ""
    client.first_name = payload.get("first_name") or client.business_name or payload.get("display_name") or "Service Client"
    client.last_name = payload.get("last_name") or ""
    client.phone = payload.get("phone") or payload.get("mobile") or "+966500000001"
    client.mobile = payload.get("mobile") or client.phone
    client.email = payload.get("email") or "client@example.com"
    client.address_line_1 = payload.get("address_line_1") or ""
    client.address_line_2 = payload.get("address_line_2") or ""
    client.city = payload.get("city") or "Riyadh"
    client.state = payload.get("state") or ""
    client.postal_code = payload.get("postal_code") or ""
    client.country = payload.get("country") or "Saudi Arabia"
    client.tax_id = payload.get("tax_id") or ""
    client.cr_number = payload.get("cr_number") or ""
    client.credit_limit = payload.get("credit_limit") or 0
    client.credit_period = payload.get("credit_period") or 30
    client.notes = payload.get("notes") or ""
    _prepare_series(client)
    saved = _save(client)
    return _doc_dict(saved, ["name", "client_type", "business_name", "first_name", "last_name", "phone", "mobile", "email", "address_line_1", "city", "country", "tax_id", "credit_limit", "credit_period"])


def create_client_contact_record(payload=None):
    payload = _payload_dict(payload)
    contact = frappe.new_doc("Client Contact")
    contact.client = payload.get("client")
    contact.contact_name = payload.get("contact_name") or payload.get("first_name") or "Contact"
    contact.phone = payload.get("phone") or ""
    contact.email = payload.get("email") or ""
    contact.position = payload.get("position") or ""
    contact.is_primary = int(payload.get("is_primary") or 0)
    _prepare_series(contact)
    saved = _save(contact)
    return _doc_dict(saved, ["name", "client", "contact_name", "phone", "email", "position", "is_primary"])


def create_appointment_record(payload=None):
    payload = _payload_dict(payload)
    appointment = frappe.new_doc("Appointment")
    appointment.client = payload.get("client")
    appointment.appointment_date = payload.get("appointment_date") or nowdate()
    appointment.appointment_time = payload.get("appointment_time") or "10:00:00"
    appointment.status = payload.get("status") or "Scheduled"
    appointment.notes = payload.get("notes") or ""
    _prepare_series(appointment)
    saved = _save(appointment)
    return _doc_dict(saved, ["name", "client", "appointment_date", "appointment_time", "status", "notes"])


def create_crm_deal_record(payload=None):
    payload = _payload_dict(payload)
    deal = frappe.new_doc("CRM Deal")
    deal.client = payload.get("client")
    deal.deal_name = payload.get("deal_name") or "New Deal"
    deal.stage = payload.get("stage") or "Lead"
    deal.expected_value = flt(payload.get("expected_value") or 0)
    deal.probability = flt(payload.get("probability") or 0)
    deal.assigned_to = payload.get("assigned_to") or frappe.session.user
    _prepare_series(deal)
    saved = _save(deal)
    return _doc_dict(saved, ["name", "client", "deal_name", "stage", "expected_value", "probability", "assigned_to"])


def create_insurance_agent_record(payload=None):
    payload = _payload_dict(payload)
    agent = frappe.new_doc("Insurance Agent")
    agent.agent_name = payload.get("agent_name") or "Insurance Agent"
    agent.phone = payload.get("phone") or ""
    agent.email = payload.get("email") or ""
    agent.commission_rate = flt(payload.get("commission_rate") or 0)
    _prepare_series(agent)
    saved = _save(agent)
    return _doc_dict(saved, ["name", "agent_name", "phone", "email", "commission_rate"])


def create_credit_type_record(payload=None):
    payload = _payload_dict(payload)
    credit_type = frappe.new_doc("Credit Type")
    credit_type.type_name = payload.get("type_name") or "Service Credit"
    credit_type.unit_label = payload.get("unit_label") or "Credits"
    credit_type.default_credits = int(payload.get("default_credits") or 0)
    credit_type.active = int(payload.get("active") if payload.get("active") is not None else 1)
    credit_type.description = payload.get("description") or ""
    _prepare_series(credit_type)
    saved = _save(credit_type)
    return _doc_dict(saved, ["name", "type_name", "unit_label", "default_credits", "active"])


def create_credit_package_record(payload=None):
    payload = _payload_dict(payload)
    package = frappe.new_doc("Credit Package")
    package.package_name = payload.get("package_name") or "Starter Package"
    package.credit_type = payload.get("credit_type")
    package.credits = int(payload.get("credits") or 0)
    package.price = flt(payload.get("price") or 0)
    package.validity_days = int(payload.get("validity_days") or 0)
    package.active = int(payload.get("active") if payload.get("active") is not None else 1)
    package.description = payload.get("description") or ""
    _prepare_series(package)
    saved = _save(package)
    return _doc_dict(saved, ["name", "package_name", "credit_type", "credits", "price", "validity_days", "active"])


def create_credit_charge_record(payload=None):
    payload = _payload_dict(payload)
    charge = frappe.new_doc("Credit Charge")
    charge.client = payload.get("client")
    charge.credit_type = payload.get("credit_type")
    charge.credit_package = payload.get("credit_package")
    charge.amount = flt(payload.get("amount") or 0)
    charge.notes = payload.get("notes") or ""
    _prepare_series(charge)
    saved = _save(charge)
    return _doc_dict(saved, ["name", "client", "credit_type", "credit_package", "amount", "notes"])


def create_credit_usage_record(payload=None):
    payload = _payload_dict(payload)
    usage = frappe.new_doc("Credit Usage")
    usage.client = payload.get("client")
    usage.credit_type = payload.get("credit_type")
    usage.credit_package = payload.get("credit_package")
    usage.reference_invoice = payload.get("reference_invoice")
    usage.amount = flt(payload.get("amount") or 0)
    usage.notes = payload.get("notes") or ""
    _prepare_series(usage)
    saved = _save(usage)
    return _doc_dict(saved, ["name", "client", "credit_type", "credit_package", "reference_invoice", "amount", "notes"])


def create_supplier_record(payload=None):
    payload = _payload_dict(payload)
    supplier = frappe.new_doc("Supplier")
    supplier.supplier_name = payload.get("supplier_name") or "Supplier"
    supplier.supplier_type = payload.get("supplier_type") or "Company"
    supplier.phone = payload.get("phone") or ""
    supplier.email = payload.get("email") or ""
    supplier.address = payload.get("address") or ""
    supplier.tax_id = payload.get("tax_id") or ""
    supplier.cr_number = payload.get("cr_number") or ""
    supplier.payment_terms = payload.get("payment_terms") or "30 Days"
    supplier.status = payload.get("status") or "Active"
    _prepare_series(supplier)
    saved = _save(supplier)
    return _doc_dict(saved, ["name", "supplier_name", "supplier_type", "phone", "email", "tax_id", "payment_terms", "status"])


def _append_purchase_item(doc, payload):
    product_name = payload.get("product")
    product_doc = frappe.get_doc("Product", product_name) if product_name else None
    qty = flt(payload.get("qty") or 1)
    rate = flt(payload.get("rate") or (product_doc.purchase_price if product_doc else 0))
    vat_rate = flt(payload.get("vat_rate") or (product_doc.vat_rate if product_doc else 0))
    doc.append("items", {
        "product": product_name,
        "description": payload.get("item_description") or (product_doc.description if product_doc else product_name),
        "qty": qty,
        "rate": rate,
        "amount": qty * rate,
        "vat_rate": vat_rate,
        "vat_amount": qty * rate * vat_rate / 100,
    })


def _copy_reference_fields(target, payload, mapping=None):
    mapping = mapping or {}
    for field in ["source_purchase_request", "source_purchase_quotation", "source_purchase_order", "sales_quotation_reference", "customer_purchase_order_no", "supplier_quotation_no", "supplier_invoice_no", "proforma_invoice_reference"]:
        source_field = mapping.get(field, field)
        if payload.get(source_field) is not None:
            setattr(target, field, payload.get(source_field))


def create_purchase_request_record(payload=None):
    payload = _payload_dict(payload)
    request = frappe.new_doc("Purchase Request")
    request.request_date = payload.get("request_date") or nowdate()
    request.requested_by = payload.get("requested_by") or frappe.session.user
    request.status = payload.get("status") or "Draft"
    _prepare_series(request)
    saved = _save(request)
    return _doc_dict(saved, ["name", "request_date", "requested_by", "status"])


def create_purchase_quotation_record(payload=None):
    payload = _payload_dict(payload)
    quotation = frappe.new_doc("Purchase Quotation")
    quotation.supplier = payload.get("supplier")
    quotation.quotation_date = payload.get("quotation_date") or nowdate()
    quotation.valid_till = payload.get("valid_till")
    quotation.currency = payload.get("currency") or frappe.get_single("Daftra Settings").default_currency or "SAR"
    quotation.status = payload.get("status") or ("Sent" if quotation.supplier else "Draft")
    quotation.notes = payload.get("notes") or ""
    _copy_reference_fields(quotation, payload)
    _prepare_series(quotation)
    if payload.get("source_purchase_request") and not payload.get("product"):
        quotation.source_purchase_request = payload.get("source_purchase_request")
    else:
        _append_purchase_item(quotation, payload)
    saved = _save(quotation)
    return _doc_dict(saved, ["name", "supplier", "quotation_date", "valid_till", "status", "total", "source_purchase_request", "sales_quotation_reference", "customer_purchase_order_no", "supplier_quotation_no", "proforma_invoice_reference"])


def create_purchase_order_record(payload=None):
    from daftra.api.procurement_api import create_purchase_order_from_quotation

    payload = _payload_dict(payload)
    if payload.get("source_purchase_quotation"):
        order_name = create_purchase_order_from_quotation(payload.get("source_purchase_quotation"))
        order = frappe.get_doc("Purchase Order", order_name)
        _copy_reference_fields(order, payload, {"source_purchase_quotation": "source_purchase_quotation"})
        if payload.get("sales_quotation_reference") and not order.sales_quotation_reference:
            order.sales_quotation_reference = payload.get("sales_quotation_reference")
        order.customer_purchase_order_no = payload.get("customer_purchase_order_no") or order.customer_purchase_order_no
        order.supplier_quotation_no = payload.get("supplier_quotation_no") or order.supplier_quotation_no
        order.proforma_invoice_reference = payload.get("proforma_invoice_reference") or order.proforma_invoice_reference
        order.notes = payload.get("notes") or order.notes
        order.save(ignore_permissions=True)
        return _doc_dict(order, ["name", "supplier", "order_date", "expected_delivery", "status", "total", "source_purchase_quotation", "sales_quotation_reference", "customer_purchase_order_no", "supplier_quotation_no", "proforma_invoice_reference"])

    order = frappe.new_doc("Purchase Order")
    order.supplier = payload.get("supplier")
    order.order_date = payload.get("order_date") or nowdate()
    order.expected_delivery = payload.get("expected_delivery")
    order.currency = payload.get("currency") or frappe.get_single("Daftra Settings").default_currency or "SAR"
    order.status = payload.get("status") or "Draft"
    order.notes = payload.get("notes") or ""
    _copy_reference_fields(order, payload)
    _prepare_series(order)
    _append_purchase_item(order, payload)
    saved = _save(order)
    return _doc_dict(saved, ["name", "supplier", "order_date", "expected_delivery", "status", "total", "source_purchase_quotation", "sales_quotation_reference", "customer_purchase_order_no", "supplier_quotation_no", "proforma_invoice_reference"])


def create_purchase_invoice_record(payload=None):
    from daftra.api.procurement_api import create_purchase_invoice_from_order

    payload = _payload_dict(payload)
    if payload.get("source_purchase_order"):
        invoice_name = create_purchase_invoice_from_order(payload.get("source_purchase_order"), submit_invoice=0)
        invoice = frappe.get_doc("Purchase Invoice", invoice_name)
        _copy_reference_fields(invoice, payload, {"source_purchase_order": "source_purchase_order", "source_purchase_quotation": "source_purchase_quotation"})
        invoice.supplier_invoice_no = payload.get("supplier_invoice_no") or invoice.supplier_invoice_no
        invoice.notes = payload.get("notes") or invoice.notes
        invoice.save(ignore_permissions=True)
        return _doc_dict(invoice, ["name", "supplier", "invoice_date", "due_date", "status", "total", "source_purchase_order", "source_purchase_quotation", "sales_quotation_reference", "customer_purchase_order_no", "supplier_invoice_no", "proforma_invoice_reference"])

    invoice = frappe.new_doc("Purchase Invoice")
    invoice.supplier = payload.get("supplier")
    invoice.invoice_date = payload.get("invoice_date") or nowdate()
    invoice.payment_terms_days = int(payload.get("payment_terms_days") or 0)
    invoice.due_date = payload.get("due_date")
    invoice.invoice_type = payload.get("invoice_type") or "Purchase"
    invoice.status = payload.get("status") or "Draft"
    invoice.notes = payload.get("notes") or ""
    _copy_reference_fields(invoice, payload)
    invoice.supplier_invoice_no = payload.get("supplier_invoice_no") or ""
    if payload.get("project"):
        invoice.project = payload.get("project")
    if payload.get("cost_center"):
        invoice.cost_center = payload.get("cost_center")
    _prepare_series(invoice)
    _append_purchase_item(invoice, payload)
    saved = _save(invoice)
    return _doc_dict(saved, ["name", "supplier", "invoice_date", "due_date", "status", "total", "source_purchase_order", "source_purchase_quotation", "sales_quotation_reference", "customer_purchase_order_no", "supplier_invoice_no", "proforma_invoice_reference"])


def create_supplier_payment_record(payload=None):
    payload = _payload_dict(payload)
    payment = frappe.new_doc("Supplier Payment")
    payment.purchase_invoice = payload.get("purchase_invoice")
    payment.payment_date = payload.get("payment_date") or nowdate()
    payment.amount = flt(payload.get("amount") or 0)
    payment.payment_method = payload.get("payment_method") or "Bank Transfer"
    payment.reference = payload.get("reference") or ""
    payment.bank_registration = payload.get("bank_registration") or frappe.db.get_value("Bank Registration", {"is_default": 1}, "name") or _demo_bank_registration().name
    payment.treasury = payload.get("treasury") or frappe.db.get_value("Treasury", {"is_active": 1}, "name") or _first_or_create("Treasury", {"treasury_name": "Main Cashbox"}, {"treasury_name": "Main Cashbox", "type": "Cash", "balance": 25000, "is_active": 1}).name
    _prepare_series(payment)
    saved = _save(payment)
    return _doc_dict(saved, ["name", "purchase_invoice", "payment_date", "payment_method", "amount", "reference"])


def create_warehouse_record(payload=None):
    payload = _payload_dict(payload)
    warehouse = frappe.new_doc("Warehouse")
    warehouse.warehouse_name = payload.get("warehouse_name") or "Warehouse"
    warehouse.location = payload.get("location") or ""
    warehouse.is_default = int(payload.get("is_default") or 0)
    warehouse.status = payload.get("status") or "Active"
    _prepare_series(warehouse)
    saved = _save(warehouse)
    return _doc_dict(saved, ["name", "warehouse_name", "location", "is_default", "status"])


def create_price_list_record(payload=None):
    payload = _payload_dict(payload)
    price_list = frappe.new_doc("Price List")
    price_list.price_list_name = payload.get("price_list_name") or "Price List"
    price_list.currency = payload.get("currency") or "SAR"
    price_list.is_default = int(payload.get("is_default") or 0)
    _prepare_series(price_list)
    saved = _save(price_list)
    return _doc_dict(saved, ["name", "price_list_name", "currency", "is_default"])


def create_price_list_rule_record(payload=None):
    payload = _payload_dict(payload)
    rule = frappe.new_doc("Price List Rule")
    rule.product = payload.get("product")
    rule.price_list = payload.get("price_list")
    rule.rate = flt(payload.get("rate") or 0)
    rule.min_qty = flt(payload.get("min_qty") or 0)
    rule.max_qty = flt(payload.get("max_qty") or 0)
    _prepare_series(rule)
    saved = _save(rule)
    return _doc_dict(saved, ["name", "product", "price_list", "rate", "min_qty", "max_qty"])


def create_stock_entry_record(payload=None):
    payload = _payload_dict(payload)
    product_name = payload.get("product")
    product_doc = frappe.get_doc("Product", product_name) if product_name else None
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.entry_type = payload.get("entry_type") or "Stock Receipt"
    stock_entry.date = payload.get("date") or nowdate()
    stock_entry.warehouse = payload.get("warehouse")
    stock_entry.notes = payload.get("notes") or ""
    _prepare_series(stock_entry)
    stock_entry.append("items", {
        "product": product_name,
        "description": payload.get("item_description") or (product_doc.product_name if product_doc else product_name),
        "qty": flt(payload.get("qty") or 1),
        "rate": flt(payload.get("rate") or (product_doc.purchase_price if product_doc else 0)),
        "amount": flt(payload.get("qty") or 1) * flt(payload.get("rate") or (product_doc.purchase_price if product_doc else 0)),
    })
    saved = _save(stock_entry, submit=1)
    return _doc_dict(saved, ["name", "entry_type", "date", "warehouse", "notes"])


def create_stocktaking_record(payload=None):
    payload = _payload_dict(payload)
    stocktaking = frappe.new_doc("Stocktaking")
    stocktaking.warehouse = payload.get("warehouse")
    stocktaking.date = payload.get("date") or nowdate()
    stocktaking.status = payload.get("status") or "Draft"
    _prepare_series(stocktaking)
    saved = _save(stocktaking)
    return _doc_dict(saved, ["name", "warehouse", "date", "status"])


def create_requisition_record(payload=None):
    payload = _payload_dict(payload)
    requisition = frappe.new_doc("Requisition")
    requisition.request_date = payload.get("request_date") or nowdate()
    requisition.requested_by = payload.get("requested_by") or frappe.session.user
    requisition.warehouse = payload.get("warehouse")
    requisition.needed_by = payload.get("needed_by")
    requisition.status = payload.get("status") or "Open"
    requisition.purpose = payload.get("purpose") or ""
    _prepare_series(requisition)
    saved = _save(requisition)
    return _doc_dict(saved, ["name", "request_date", "requested_by", "warehouse", "needed_by", "status", "purpose"])


def create_product_record(payload=None):
    payload = _payload_dict(payload)
    product = frappe.new_doc("Product")
    product.product_code = payload.get("product_code") or f"PRD-{frappe.generate_hash(length=6).upper()}"
    product.product_name = payload.get("product_name") or payload.get("description") or "Product"
    product.category = payload.get("category") or ("Services" if payload.get("product_type") == "Service" else "General")
    product.brand = payload.get("brand") or "Daftra"
    product.product_type = payload.get("product_type") or "Product"
    product.unit_of_measure = payload.get("unit_of_measure") or ("SVC" if product.product_type == "Service" else "PCS")
    product.barcode = payload.get("barcode") or ""
    product.sku = payload.get("sku") or ""
    product.purchase_price = flt(payload.get("purchase_price") or 0)
    product.selling_price = flt(payload.get("selling_price") or 0)
    product.wholesale_price = flt(payload.get("wholesale_price") or product.selling_price)
    product.opening_stock = flt(payload.get("opening_stock") or 0)
    product.current_stock = flt(payload.get("current_stock") or product.opening_stock)
    product.minimum_stock = flt(payload.get("minimum_stock") or 0)
    product.maximum_stock = flt(payload.get("maximum_stock") or 0)
    product.vat_rate = flt(payload.get("vat_rate") or 15)
    product.status = payload.get("status") or "Active"
    product.description = payload.get("description") or product.product_name
    _prepare_series(product)
    saved = _save(product)
    return _doc_dict(saved, ["name", "product_code", "product_name", "product_type", "unit_of_measure", "selling_price", "vat_rate", "current_stock", "status", "description"])


@frappe.whitelist()
def create_service_product(payload=None):
    payload = _payload_dict(payload)
    payload["product_type"] = "Service"
    payload.setdefault("category", "Services")
    payload.setdefault("unit_of_measure", "SVC")
    return create_product_record(payload)


@frappe.whitelist()
def create_service_booking(payload=None):
    payload = _payload_dict(payload)
    booking = frappe.new_doc("Booking")
    booking.client = payload.get("client")
    booking.booking_date = payload.get("booking_date") or nowdate()
    booking.booking_time = payload.get("booking_time") or "10:00:00"
    booking.service = payload.get("service") or "Maintenance"
    booking.status = payload.get("status") or "Confirmed"
    booking.notes = payload.get("notes") or (f"Project: {payload.get('project')}" if payload.get("project") else "Booked from Daftra service flow")
    _prepare_series(booking)
    saved = _save(booking)
    return _doc_dict(saved, ["name", "client", "booking_date", "booking_time", "service", "status"])


@frappe.whitelist()
def create_time_entry_record(payload=None):
    payload = _payload_dict(payload)
    time_entry = frappe.new_doc("Time Entry")
    time_entry.employee = payload.get("employee")
    time_entry.client = payload.get("client")
    time_entry.project = payload.get("project")
    time_entry.cost_center = payload.get("cost_center")
    time_entry.task = payload.get("task") or "Service delivery"
    time_entry.date = payload.get("date") or nowdate()
    time_entry.start_time = payload.get("start_time") or "09:00:00"
    time_entry.end_time = payload.get("end_time") or "11:00:00"
    time_entry.duration_hours = flt(payload.get("duration_hours") or 2)
    time_entry.hourly_rate = flt(payload.get("hourly_rate") or 250)
    time_entry.cost_rate = flt(payload.get("cost_rate") or time_entry.hourly_rate)
    time_entry.billable_amount = flt(payload.get("billable_amount") or time_entry.duration_hours * time_entry.hourly_rate)
    time_entry.cost_amount = flt(payload.get("cost_amount") or time_entry.duration_hours * time_entry.cost_rate)
    time_entry.is_billed = int(payload.get("is_billed") or 0)
    time_entry.notes = payload.get("notes") or "Demo billable time entry"
    _prepare_series(time_entry)
    saved = _save(time_entry)
    return _doc_dict(saved, ["name", "employee", "client", "project", "cost_center", "task", "date", "duration_hours", "hourly_rate", "cost_rate", "billable_amount", "cost_amount", "is_billed"])


@frappe.whitelist()
def get_frontend_boot():
    from daftra.api.dashboard_api import get_dashboard_blueprint, get_dashboard_overview, get_document_catalog

    overview = get_dashboard_overview()

    return {
        **overview,
        "enabled_modules": overview.get("modules", {}),
        "modules": MODULE_MAP,
        "scenarios": SCENARIOS,
        "low_stock": get_low_stock(),
        "recent_activity": get_recent_activity(),
        "document_catalog": get_document_catalog(),
        "blueprint": get_dashboard_blueprint(),
    }


WORKSPACE_CONFIG = {
    "Client": {
        "module": "Clients",
        "title_field": "business_name",
        "list_fields": ["name", "business_name", "first_name", "client_type", "phone", "email", "city", "tax_id", "modified"],
        "detail_fields": ["name", "client_type", "business_name", "first_name", "last_name", "phone", "mobile", "email", "address_line_1", "address_line_2", "city", "state", "postal_code", "country", "tax_id", "cr_number", "credit_limit", "credit_period", "notes"],
        "create_fields": [
            {"fieldname": "client_type", "label": "Client Type", "type": "Select", "options": ["Business", "Individual"]},
            {"fieldname": "business_name", "label": "Business Name", "type": "Data"},
            {"fieldname": "first_name", "label": "Primary Contact", "type": "Data", "required": 1},
            {"fieldname": "last_name", "label": "Last Name", "type": "Data"},
            {"fieldname": "email", "label": "Email", "type": "Data"},
            {"fieldname": "phone", "label": "Phone", "type": "Data"},
            {"fieldname": "mobile", "label": "Mobile", "type": "Data"},
            {"fieldname": "address_line_1", "label": "Address Line 1", "type": "Data"},
            {"fieldname": "city", "label": "City", "type": "Data"},
            {"fieldname": "country", "label": "Country", "type": "Data"},
            {"fieldname": "tax_id", "label": "VAT / Tax ID", "type": "Data"},
            {"fieldname": "credit_limit", "label": "Credit Limit", "type": "Currency"},
            {"fieldname": "credit_period", "label": "Credit Period", "type": "Int"},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Client Contact": {
        "module": "Clients",
        "label": "Contacts",
        "title_field": "contact_name",
        "list_fields": ["name", "client", "contact_name", "phone", "email", "position", "modified"],
        "detail_fields": ["name", "client", "contact_name", "phone", "email", "position", "is_primary"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients", "required": 1},
            {"fieldname": "contact_name", "label": "Contact Name", "type": "Data", "required": 1},
            {"fieldname": "phone", "label": "Phone", "type": "Data"},
            {"fieldname": "email", "label": "Email", "type": "Data"},
            {"fieldname": "position", "label": "Position", "type": "Data"},
            {"fieldname": "is_primary", "label": "Primary Contact", "type": "Check"},
        ],
    },
    "Appointment": {
        "module": "Clients",
        "title_field": "client",
        "list_fields": ["name", "client", "appointment_date", "appointment_time", "status", "modified"],
        "detail_fields": ["name", "client", "appointment_date", "appointment_time", "status", "notes"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients", "required": 1},
            {"fieldname": "appointment_date", "label": "Date", "type": "Date", "required": 1},
            {"fieldname": "appointment_time", "label": "Time", "type": "Time"},
            {"fieldname": "status", "label": "Status", "type": "Select", "options": ["Scheduled", "Completed", "Cancelled", "No Show"]},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "CRM Deal": {
        "module": "Clients",
        "title_field": "deal_name",
        "list_fields": ["name", "deal_name", "client", "stage", "expected_value", "probability", "modified"],
        "detail_fields": ["name", "deal_name", "client", "stage", "expected_value", "probability", "assigned_to"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients"},
            {"fieldname": "deal_name", "label": "Deal Name", "type": "Data", "required": 1},
            {"fieldname": "stage", "label": "Stage", "type": "Select", "options": ["Lead", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]},
            {"fieldname": "expected_value", "label": "Expected Value", "type": "Currency"},
            {"fieldname": "probability", "label": "Probability", "type": "Percent"},
        ],
    },
    "Insurance Agent": {
        "module": "Clients",
        "title_field": "agent_name",
        "list_fields": ["name", "agent_name", "phone", "email", "commission_rate", "modified"],
        "detail_fields": ["name", "agent_name", "phone", "email", "commission_rate"],
        "create_fields": [
            {"fieldname": "agent_name", "label": "Agent Name", "type": "Data", "required": 1},
            {"fieldname": "phone", "label": "Phone", "type": "Data"},
            {"fieldname": "email", "label": "Email", "type": "Data"},
            {"fieldname": "commission_rate", "label": "Commission Rate", "type": "Percent"},
        ],
    },
    "Credit Type": {
        "module": "Clients",
        "title_field": "type_name",
        "list_fields": ["name", "type_name", "unit_label", "default_credits", "active", "modified"],
        "detail_fields": ["name", "type_name", "unit_label", "default_credits", "active", "description"],
        "create_fields": [
            {"fieldname": "type_name", "label": "Type Name", "type": "Data", "required": 1},
            {"fieldname": "unit_label", "label": "Unit Label", "type": "Data"},
            {"fieldname": "default_credits", "label": "Default Credits", "type": "Int"},
            {"fieldname": "active", "label": "Active", "type": "Check"},
            {"fieldname": "description", "label": "Description", "type": "Text"},
        ],
    },
    "Credit Package": {
        "module": "Clients",
        "title_field": "package_name",
        "list_fields": ["name", "package_name", "credit_type", "credits", "price", "active", "modified"],
        "detail_fields": ["name", "package_name", "credit_type", "credits", "price", "validity_days", "active", "description"],
        "create_fields": [
            {"fieldname": "package_name", "label": "Package Name", "type": "Data", "required": 1},
            {"fieldname": "credit_type", "label": "Credit Type", "type": "Link", "options_key": "credit_types"},
            {"fieldname": "credits", "label": "Credits", "type": "Int"},
            {"fieldname": "price", "label": "Price", "type": "Currency"},
            {"fieldname": "validity_days", "label": "Validity Days", "type": "Int"},
            {"fieldname": "active", "label": "Active", "type": "Check"},
            {"fieldname": "description", "label": "Description", "type": "Text"},
        ],
    },
    "Credit Charge": {
        "module": "Clients",
        "title_field": "name",
        "list_fields": ["name", "client", "credit_type", "credit_package", "amount", "modified"],
        "detail_fields": ["name", "client", "credit_type", "credit_package", "amount", "notes"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients", "required": 1},
            {"fieldname": "credit_type", "label": "Credit Type", "type": "Link", "options_key": "credit_types"},
            {"fieldname": "credit_package", "label": "Credit Package", "type": "Link", "options_key": "credit_packages"},
            {"fieldname": "amount", "label": "Amount", "type": "Currency", "required": 1},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Credit Usage": {
        "module": "Clients",
        "title_field": "name",
        "list_fields": ["name", "client", "credit_type", "reference_invoice", "amount", "modified"],
        "detail_fields": ["name", "client", "credit_type", "credit_package", "reference_invoice", "amount", "notes"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients", "required": 1},
            {"fieldname": "credit_type", "label": "Credit Type", "type": "Link", "options_key": "credit_types"},
            {"fieldname": "credit_package", "label": "Credit Package", "type": "Link", "options_key": "credit_packages"},
            {"fieldname": "reference_invoice", "label": "Reference Invoice", "type": "Link", "options_key": "invoices"},
            {"fieldname": "amount", "label": "Amount", "type": "Currency", "required": 1},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Daftra Project": {
        "module": "Projects",
        "title_field": "project_name",
        "list_fields": ["name", "project_code", "project_name", "client", "status", "expected_revenue", "modified"],
        "detail_fields": ["name", "project_code", "project_name", "client", "project_type", "status", "start_date", "end_date", "budget_amount", "expected_revenue", "project_cost_center", "actual_revenue", "actual_cost", "profit", "margin_percent", "description", "notes"],
        "create_fields": [
            {"fieldname": "project_code", "label": "Project Code", "type": "Data"},
            {"fieldname": "project_name", "label": "Project Name", "type": "Data", "required": 1},
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients"},
            {"fieldname": "project_type", "label": "Type", "type": "Select", "options": ["Service Project", "Contract", "Maintenance", "Installation", "Trading", "Mixed"]},
            {"fieldname": "status", "label": "Status", "type": "Select", "options": ["Draft", "Active", "On Hold", "Completed", "Closed"]},
            {"fieldname": "budget_amount", "label": "Budget Amount", "type": "Currency"},
            {"fieldname": "expected_revenue", "label": "Expected Revenue", "type": "Currency"},
            {"fieldname": "description", "label": "Description", "type": "Text"},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Product": {
        "module": "Inventory",
        "title_field": "product_name",
        "list_fields": ["name", "product_code", "product_name", "product_type", "category", "selling_price", "vat_rate", "status", "modified"],
        "detail_fields": ["name", "product_code", "product_name", "product_type", "category", "brand", "unit_of_measure", "selling_price", "purchase_price", "vat_rate", "current_stock", "minimum_stock", "status", "description"],
        "create_fields": [
            {"fieldname": "product_code", "label": "Product Code", "type": "Data"},
            {"fieldname": "product_name", "label": "Product Name", "type": "Data", "required": 1},
            {"fieldname": "product_type", "label": "Type", "type": "Select", "options": ["Product", "Service", "Digital"]},
            {"fieldname": "category", "label": "Category", "type": "Data"},
            {"fieldname": "selling_price", "label": "Selling Price", "type": "Currency"},
            {"fieldname": "vat_rate", "label": "VAT %", "type": "Percent"},
            {"fieldname": "status", "label": "Status", "type": "Select", "options": ["Active", "Inactive", "Discontinued"]},
            {"fieldname": "description", "label": "Description", "type": "Text"},
        ],
    },
    "Warehouse": {
        "module": "Inventory",
        "title_field": "warehouse_name",
        "list_fields": ["name", "warehouse_name", "location", "is_default", "status", "modified"],
        "detail_fields": ["name", "warehouse_name", "location", "is_default", "status"],
        "create_fields": [
            {"fieldname": "warehouse_name", "label": "Warehouse Name", "type": "Data", "required": 1},
            {"fieldname": "location", "label": "Location", "type": "Data"},
            {"fieldname": "is_default", "label": "Default Warehouse", "type": "Check"},
            {"fieldname": "status", "label": "Status", "type": "Select", "options": ["Active", "Inactive"]},
        ],
    },
    "Price List": {
        "module": "Inventory",
        "title_field": "price_list_name",
        "list_fields": ["name", "price_list_name", "currency", "is_default", "modified"],
        "detail_fields": ["name", "price_list_name", "currency", "is_default"],
        "create_fields": [
            {"fieldname": "price_list_name", "label": "Price List Name", "type": "Data", "required": 1},
            {"fieldname": "currency", "label": "Currency", "type": "Select", "options": ["SAR", "AED", "USD", "PKR"]},
            {"fieldname": "is_default", "label": "Default", "type": "Check"},
        ],
    },
    "Price List Rule": {
        "module": "Inventory",
        "title_field": "name",
        "list_fields": ["name", "product", "price_list", "rate", "min_qty", "max_qty", "modified"],
        "detail_fields": ["name", "product", "price_list", "rate", "min_qty", "max_qty"],
        "create_fields": [
            {"fieldname": "product", "label": "Product", "type": "Link", "options_key": "products", "required": 1},
            {"fieldname": "price_list", "label": "Price List", "type": "Link", "options_key": "price_lists", "required": 1},
            {"fieldname": "rate", "label": "Rate", "type": "Currency", "required": 1},
            {"fieldname": "min_qty", "label": "Min Qty", "type": "Float"},
            {"fieldname": "max_qty", "label": "Max Qty", "type": "Float"},
        ],
    },
    "Stock Entry": {
        "module": "Inventory",
        "title_field": "name",
        "list_fields": ["name", "entry_type", "date", "warehouse", "modified"],
        "detail_fields": ["name", "entry_type", "date", "warehouse", "notes"],
        "create_fields": [
            {"fieldname": "entry_type", "label": "Entry Type", "type": "Select", "options": ["Stock Receipt", "Stock Issue", "Stock Transfer", "Stock Adjustment"], "required": 1},
            {"fieldname": "date", "label": "Date", "type": "Date", "required": 1},
            {"fieldname": "warehouse", "label": "Warehouse", "type": "Link", "options_key": "warehouses"},
            {"fieldname": "product", "label": "Product", "type": "Link", "options_key": "products", "required": 1},
            {"fieldname": "qty", "label": "Quantity", "type": "Float", "required": 1},
            {"fieldname": "rate", "label": "Rate", "type": "Currency", "required": 1},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Stocktaking": {
        "module": "Inventory",
        "title_field": "name",
        "list_fields": ["name", "warehouse", "date", "status", "modified"],
        "detail_fields": ["name", "warehouse", "date", "status"],
        "create_fields": [
            {"fieldname": "warehouse", "label": "Warehouse", "type": "Link", "options_key": "warehouses", "required": 1},
            {"fieldname": "date", "label": "Date", "type": "Date", "required": 1},
            {"fieldname": "status", "label": "Status", "type": "Select", "options": ["Draft", "In Progress", "Completed", "Cancelled"]},
        ],
    },
    "Requisition": {
        "module": "Inventory",
        "title_field": "name",
        "list_fields": ["name", "request_date", "requested_by", "warehouse", "needed_by", "status", "modified"],
        "detail_fields": ["name", "request_date", "requested_by", "warehouse", "needed_by", "status", "purpose"],
        "create_fields": [
            {"fieldname": "request_date", "label": "Request Date", "type": "Date", "required": 1},
            {"fieldname": "requested_by", "label": "Requested By", "type": "Link", "options_key": "users"},
            {"fieldname": "warehouse", "label": "Warehouse", "type": "Link", "options_key": "warehouses"},
            {"fieldname": "needed_by", "label": "Needed By", "type": "Date"},
            {"fieldname": "status", "label": "Status", "type": "Select", "options": ["Draft", "Open", "Approved", "Ordered", "Closed", "Cancelled"]},
            {"fieldname": "purpose", "label": "Purpose", "type": "Text"},
        ],
    },
    "Supplier": {
        "module": "Purchases",
        "title_field": "supplier_name",
        "list_fields": ["name", "supplier_name", "supplier_type", "phone", "email", "status", "modified"],
        "detail_fields": ["name", "supplier_name", "supplier_type", "phone", "email", "address", "tax_id", "cr_number", "payment_terms", "status"],
        "create_fields": [
            {"fieldname": "supplier_name", "label": "Supplier Name", "type": "Data", "required": 1},
            {"fieldname": "supplier_type", "label": "Type", "type": "Select", "options": ["Company", "Individual"]},
            {"fieldname": "phone", "label": "Phone", "type": "Data"},
            {"fieldname": "email", "label": "Email", "type": "Data"},
            {"fieldname": "address", "label": "Address", "type": "Text"},
            {"fieldname": "tax_id", "label": "Tax ID", "type": "Data"},
            {"fieldname": "payment_terms", "label": "Payment Terms", "type": "Select", "options": ["Cash", "7 Days", "15 Days", "30 Days", "45 Days", "60 Days"]},
            {"fieldname": "status", "label": "Status", "type": "Select", "options": ["Active", "Inactive", "Blocked"]},
        ],
    },
    "Purchase Request": {
        "module": "Purchases",
        "title_field": "name",
        "list_fields": ["name", "request_date", "requested_by", "status", "modified"],
        "detail_fields": ["name", "request_date", "requested_by", "status"],
        "create_fields": [
            {"fieldname": "request_date", "label": "Date", "type": "Date", "required": 1},
            {"fieldname": "requested_by", "label": "Requested By", "type": "Link", "options_key": "users"},
            {"fieldname": "status", "label": "Status", "type": "Select", "options": ["Draft", "Approved", "Ordered", "Rejected"]},
        ],
    },
    "Purchase Quotation": {
        "module": "Purchases",
        "title_field": "name",
        "list_fields": ["name", "supplier", "quotation_date", "valid_till", "status", "total", "modified"],
        "detail_fields": ["name", "supplier", "quotation_date", "valid_till", "currency", "status", "subtotal", "tax_amount", "total", "source_purchase_request", "sales_quotation_reference", "customer_purchase_order_no", "supplier_quotation_no", "proforma_invoice_reference", "notes"],
        "create_fields": [
            {"fieldname": "supplier", "label": "Supplier", "type": "Link", "options_key": "suppliers"},
            {"fieldname": "product", "label": "Product", "type": "Link", "options_key": "products", "required": 1},
            {"fieldname": "qty", "label": "Quantity", "type": "Float", "required": 1},
            {"fieldname": "rate", "label": "Rate", "type": "Currency", "required": 1},
            {"fieldname": "valid_till", "label": "Valid Till", "type": "Date"},
            {"fieldname": "source_purchase_request", "label": "Source Purchase Request", "type": "Link", "options_key": "purchase_requests"},
            {"fieldname": "sales_quotation_reference", "label": "Sales Quotation Reference", "type": "Link", "options_key": "sales_quotations"},
            {"fieldname": "customer_purchase_order_no", "label": "Customer Purchase Order No", "type": "Data"},
            {"fieldname": "supplier_quotation_no", "label": "Supplier Quotation No", "type": "Data"},
            {"fieldname": "proforma_invoice_reference", "label": "Proforma Invoice Reference", "type": "Data"},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Purchase Order": {
        "module": "Purchases",
        "title_field": "name",
        "list_fields": ["name", "supplier", "order_date", "expected_delivery", "status", "total", "modified"],
        "detail_fields": ["name", "supplier", "order_date", "expected_delivery", "currency", "status", "subtotal", "tax_amount", "total", "source_purchase_quotation", "sales_quotation_reference", "customer_purchase_order_no", "supplier_quotation_no", "proforma_invoice_reference", "notes"],
        "create_fields": [
            {"fieldname": "supplier", "label": "Supplier", "type": "Link", "options_key": "suppliers", "required": 1},
            {"fieldname": "product", "label": "Product", "type": "Link", "options_key": "products", "required": 1},
            {"fieldname": "qty", "label": "Quantity", "type": "Float", "required": 1},
            {"fieldname": "rate", "label": "Rate", "type": "Currency", "required": 1},
            {"fieldname": "expected_delivery", "label": "Expected Delivery", "type": "Date"},
            {"fieldname": "source_purchase_quotation", "label": "Source Purchase Quotation", "type": "Link", "options_key": "purchase_quotations"},
            {"fieldname": "sales_quotation_reference", "label": "Sales Quotation Reference", "type": "Link", "options_key": "sales_quotations"},
            {"fieldname": "customer_purchase_order_no", "label": "Customer Purchase Order No", "type": "Data"},
            {"fieldname": "supplier_quotation_no", "label": "Supplier Quotation No", "type": "Data"},
            {"fieldname": "proforma_invoice_reference", "label": "Proforma Invoice Reference", "type": "Data"},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Purchase Invoice": {
        "module": "Purchases",
        "title_field": "name",
        "list_fields": ["name", "supplier", "invoice_date", "due_date", "status", "total", "paid_amount", "modified"],
        "detail_fields": ["name", "supplier", "invoice_date", "due_date", "invoice_type", "status", "subtotal", "tax_amount", "total", "paid_amount", "source_purchase_order", "source_purchase_quotation", "sales_quotation_reference", "customer_purchase_order_no", "supplier_invoice_no", "proforma_invoice_reference", "notes", "project", "cost_center"],
        "create_fields": [
            {"fieldname": "supplier", "label": "Supplier", "type": "Link", "options_key": "suppliers", "required": 1},
            {"fieldname": "product", "label": "Product", "type": "Link", "options_key": "products", "required": 1},
            {"fieldname": "qty", "label": "Quantity", "type": "Float", "required": 1},
            {"fieldname": "rate", "label": "Rate", "type": "Currency", "required": 1},
            {"fieldname": "payment_terms_days", "label": "Payment Terms (Days)", "type": "Int"},
            {"fieldname": "source_purchase_order", "label": "Source Purchase Order", "type": "Link", "options_key": "purchase_orders"},
            {"fieldname": "source_purchase_quotation", "label": "Source Purchase Quotation", "type": "Link", "options_key": "purchase_quotations"},
            {"fieldname": "sales_quotation_reference", "label": "Sales Quotation Reference", "type": "Link", "options_key": "sales_quotations"},
            {"fieldname": "customer_purchase_order_no", "label": "Customer Purchase Order No", "type": "Data"},
            {"fieldname": "supplier_invoice_no", "label": "Supplier Invoice No", "type": "Data"},
            {"fieldname": "proforma_invoice_reference", "label": "Proforma Invoice Reference", "type": "Data"},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Supplier Payment": {
        "module": "Purchases",
        "title_field": "name",
        "list_fields": ["name", "purchase_invoice", "payment_date", "payment_method", "amount", "reference", "modified"],
        "detail_fields": ["name", "purchase_invoice", "payment_date", "payment_method", "bank_registration", "treasury", "amount", "reference"],
        "create_fields": [
            {"fieldname": "purchase_invoice", "label": "Purchase Invoice", "type": "Link", "options_key": "purchase_invoices", "required": 1},
            {"fieldname": "payment_date", "label": "Payment Date", "type": "Date", "required": 1},
            {"fieldname": "amount", "label": "Amount", "type": "Currency", "required": 1},
            {"fieldname": "payment_method", "label": "Method", "type": "Select", "options": ["Cash", "Bank Transfer", "Card", "Cheque", "Online"]},
            {"fieldname": "reference", "label": "Reference", "type": "Data"},
        ],
    },
    "Booking": {
        "module": "Bookings",
        "title_field": "service",
        "list_fields": ["name", "client", "booking_date", "booking_time", "service", "status", "modified"],
        "detail_fields": ["name", "client", "booking_date", "booking_time", "service", "status", "notes"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients", "required": 1},
            {"fieldname": "booking_date", "label": "Booking Date", "type": "Date", "required": 1},
            {"fieldname": "booking_time", "label": "Booking Time", "type": "Time"},
            {"fieldname": "service", "label": "Service", "type": "Data", "required": 1},
            {"fieldname": "status", "label": "Status", "type": "Select", "options": ["Pending", "Confirmed", "Completed", "Cancelled", "No Show"]},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Time Entry": {
        "module": "Time Tracking",
        "title_field": "task",
        "list_fields": ["name", "client", "task", "date", "duration_hours", "hourly_rate", "billable_amount", "modified"],
        "detail_fields": ["name", "employee", "client", "task", "date", "start_time", "end_time", "duration_hours", "hourly_rate", "billable_amount", "project", "cost_center", "cost_rate", "cost_amount", "notes"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients"},
            {"fieldname": "project", "label": "Project", "type": "Link", "options_key": "projects"},
            {"fieldname": "task", "label": "Task", "type": "Data", "required": 1},
            {"fieldname": "date", "label": "Date", "type": "Date", "required": 1},
            {"fieldname": "duration_hours", "label": "Duration Hours", "type": "Float"},
            {"fieldname": "hourly_rate", "label": "Hourly Rate", "type": "Currency"},
            {"fieldname": "cost_rate", "label": "Cost Rate", "type": "Currency"},
            {"fieldname": "is_billed", "label": "Billed", "type": "Check"},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Sales Invoice": {
        "module": "Sales",
        "label": "Invoices",
        "title_field": "name",
        "list_fields": ["name", "client", "invoice_date", "due_date", "invoice_layout", "status", "total", "balance", "modified"],
        "detail_fields": ["name", "client", "invoice_date", "due_date", "invoice_layout", "payment_method", "status", "subtotal", "tax_amount", "total", "balance", "description_of_work", "project_title", "project_reference", "project_scope", "contract_acknowledgement", "notes"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients", "required": 1},
            {"fieldname": "item", "label": "Item / Service", "type": "Link", "options_key": "products", "required": 1},
            {"fieldname": "qty", "label": "Quantity", "type": "Float", "required": 1},
            {"fieldname": "rate", "label": "Rate", "type": "Currency", "required": 1},
            {"fieldname": "vat_rate", "label": "VAT %", "type": "Percent"},
            {"fieldname": "invoice_layout", "label": "Invoice Layout", "type": "Select", "options": ["Materials & Services", "Default Invoice", "TAX Invoice", "Receipt"]},
            {"fieldname": "due_date", "label": "Due Date", "type": "Date"},
            {"fieldname": "description_of_work", "label": "Description of Work", "type": "Text"},
            {"fieldname": "project_title", "label": "Project Title", "type": "Data"},
            {"fieldname": "project_reference", "label": "Project Reference", "type": "Data"},
            {"fieldname": "project_scope", "label": "Project Scope", "type": "Text"},
            {"fieldname": "contract_acknowledgement", "label": "Contractor Acknowledgement", "type": "Text"},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Sales Quotation": {
        "module": "Sales",
        "label": "Quotations",
        "title_field": "name",
        "list_fields": ["name", "client", "quotation_date", "valid_till", "status", "total", "modified"],
        "detail_fields": ["name", "client", "quotation_date", "valid_till", "currency", "status", "subtotal", "discount_amount", "tax_amount", "total", "notes"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients", "required": 1},
            {"fieldname": "item", "label": "Item / Service", "type": "Link", "options_key": "products", "required": 1},
            {"fieldname": "qty", "label": "Quantity", "type": "Float", "required": 1},
            {"fieldname": "rate", "label": "Rate", "type": "Currency", "required": 1},
            {"fieldname": "vat_rate", "label": "VAT %", "type": "Percent"},
            {"fieldname": "valid_till", "label": "Valid Till", "type": "Date"},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Invoice Payment": {
        "module": "Sales",
        "label": "Client Payments",
        "title_field": "name",
        "list_fields": ["name", "sales_invoice", "payment_date", "payment_method", "amount", "reference", "modified"],
        "detail_fields": ["name", "sales_invoice", "payment_date", "payment_method", "bank_registration", "treasury", "amount", "reference"],
        "create_fields": [
            {"fieldname": "sales_invoice", "label": "Invoice", "type": "Link", "options_key": "invoices", "required": 1},
            {"fieldname": "payment_date", "label": "Payment Date", "type": "Date", "required": 1},
            {"fieldname": "amount", "label": "Amount", "type": "Currency", "required": 1},
            {"fieldname": "payment_method", "label": "Method", "type": "Select", "options": ["Cash", "Bank Transfer", "Card", "Cheque", "Online"]},
            {"fieldname": "reference", "label": "Reference", "type": "Data"},
        ],
    },
    "Recurring Invoice": {
        "module": "Sales",
        "label": "Recurring Invoices",
        "title_field": "name",
        "list_fields": ["name", "client", "frequency", "start_date", "next_invoice_date", "total_amount", "status", "modified"],
        "detail_fields": ["name", "client", "frequency", "start_date", "end_date", "next_invoice_date", "total_amount", "status"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients", "required": 1},
            {"fieldname": "frequency", "label": "Frequency", "type": "Select", "options": ["Monthly", "Quarterly", "Yearly"], "required": 1},
            {"fieldname": "start_date", "label": "Start Date", "type": "Date", "required": 1},
            {"fieldname": "end_date", "label": "End Date", "type": "Date"},
            {"fieldname": "total_amount", "label": "Amount", "type": "Currency"},
            {"fieldname": "status", "label": "Status", "type": "Select", "options": ["Active", "Paused", "Completed", "Cancelled"]},
        ],
    },
}


def _resolve_workspace_config(doctype=None, view_key=None):
    actual_doctype = doctype or WORKSPACE_VIEW_ALIASES.get(view_key)
    config = WORKSPACE_CONFIG.get(actual_doctype)
    if not config:
        frappe.throw(_("Unsupported workspace doctype"))
    config = {**config}
    config["doctype"] = actual_doctype
    config["view_key"] = view_key or frappe.scrub(actual_doctype)
    if view_key == "credit_notes":
        config["label"] = "Credit Notes"
        config["filters"] = {"invoice_type": "Credit Note"}
    elif view_key == "refund_receipts":
        config["label"] = "Refund Receipts"
        config["filters"] = {"invoice_type": "Refund"}
    elif view_key == "sales_invoices":
        config["label"] = "Invoices"
        config["filters"] = {"invoice_type": "Normal"}
    return config


def _workspace_options():
    return {
        "clients": frappe.get_all("Client", fields=["name", "business_name", "first_name", "last_name", "tax_id"], order_by="modified desc", limit_page_length=100),
        "products": frappe.get_all("Product", fields=["name", "product_code", "product_name", "product_type", "selling_price", "vat_rate"], order_by="modified desc", limit_page_length=100),
        "projects": frappe.get_all("Daftra Project", fields=["name", "project_code", "project_name", "client", "status", "project_cost_center"], order_by="modified desc", limit_page_length=100),
        "employees": frappe.get_all("Employee", fields=["name", "employee_name", "employee_id", "email"], order_by="modified desc", limit_page_length=100),
        "warehouses": frappe.get_all("Warehouse", fields=["name", "warehouse_name", "location", "is_default", "status"], order_by="modified desc", limit_page_length=100),
        "price_lists": frappe.get_all("Price List", fields=["name", "price_list_name", "currency", "is_default"], order_by="modified desc", limit_page_length=100),
        "suppliers": frappe.get_all("Supplier", fields=["name", "supplier_name", "supplier_type", "phone", "email", "payment_terms"], order_by="modified desc", limit_page_length=100),
        "sales_quotations": frappe.get_all("Sales Quotation", fields=["name", "client", "quotation_date", "total", "status"], order_by="modified desc", limit_page_length=100),
        "purchase_quotations": frappe.get_all("Purchase Quotation", fields=["name", "supplier", "quotation_date", "total", "status"], order_by="modified desc", limit_page_length=100),
        "purchase_orders": frappe.get_all("Purchase Order", fields=["name", "supplier", "order_date", "total", "status"], order_by="modified desc", limit_page_length=100),
        "purchase_requests": frappe.get_all("Purchase Request", fields=["name", "request_date", "requested_by", "status"], order_by="modified desc", limit_page_length=100),
        "purchase_invoices": frappe.get_all("Purchase Invoice", fields=["name", "supplier", "invoice_date", "total", "paid_amount", "status"], order_by="modified desc", limit_page_length=100),
        "invoices": frappe.get_all("Sales Invoice", fields=["name", "client", "total", "balance", "status"], order_by="modified desc", limit_page_length=100),
        "credit_types": frappe.get_all("Credit Type", fields=["name", "type_name", "unit_label", "default_credits", "active"], order_by="modified desc", limit_page_length=100),
        "credit_packages": frappe.get_all("Credit Package", fields=["name", "package_name", "credit_type", "credits", "price", "active"], order_by="modified desc", limit_page_length=100),
        "insurance_agents": frappe.get_all("Insurance Agent", fields=["name", "agent_name", "commission_rate", "email"], order_by="modified desc", limit_page_length=100),
        "users": frappe.get_all("User", fields=["name", "full_name", "email"], filters={"enabled": 1}, order_by="modified desc", limit_page_length=100),
    }


def _record_summary(doctype, row, config):
    title_field = config.get("title_field")
    title = row.get(title_field) or row.get("name")
    subtitle_parts = []
    for key in config.get("list_fields", [])[1:4]:
        value = row.get(key)
        if value and value != title:
            subtitle_parts.append(str(value))
    amount = row.get("total") or row.get("selling_price") or row.get("billable_amount")
    return {**row, "title": title, "subtitle": " · ".join(subtitle_parts), "amount": amount}


def create_sales_invoice_record(payload=None):
    from daftra.api.sales_api import validate_sales_invoice_payload

    payload = _payload_dict(payload)
    item_name = payload.get("item") or payload.get("product")
    item_doc = frappe.get_doc("Product", item_name) if item_name else None
    rate = flt(payload.get("rate") or (item_doc.selling_price if item_doc else 0))
    vat_rate = flt(payload.get("vat_rate") or (item_doc.vat_rate if item_doc else 15))
    qty = flt(payload.get("qty") or 1)
    validation = validate_sales_invoice_payload({
        "client": payload.get("client"),
        "invoice_layout": payload.get("invoice_layout") or "Materials & Services",
        "description_of_work": payload.get("description_of_work") or payload.get("project_scope") or payload.get("notes") or (item_doc.description if item_doc else ""),
        "notes": payload.get("notes"),
        "due_date": payload.get("due_date"),
        "items": [{"qty": qty, "rate": rate, "vat_rate": vat_rate}],
        "discount_amount": payload.get("discount_amount") or 0,
        "deposit_amount": payload.get("deposit_amount") or 0,
        "adjustment_amount": payload.get("adjustment_amount") or 0,
    })
    if not validation.get("ok"):
        frappe.throw("; ".join(validation.get("errors") or []))

    invoice = frappe.new_doc("Sales Invoice")
    invoice.client = payload.get("client")
    invoice.invoice_date = payload.get("invoice_date") or nowdate()
    invoice.due_date = payload.get("due_date") or add_days(invoice.invoice_date, 30)
    invoice.currency = payload.get("currency") or frappe.get_single("Daftra Settings").default_currency or "SAR"
    invoice.invoice_type = payload.get("invoice_type") or "Normal"
    invoice.status = payload.get("status") or "Draft"
    invoice.payment_method = payload.get("payment_method") or "Bank Transfer"
    invoice.invoice_layout = payload.get("invoice_layout") or "Materials & Services"
    invoice.notes = payload.get("notes") or ""
    invoice.project = payload.get("project") or None
    invoice.cost_center = payload.get("cost_center") or None
    invoice.description_of_work = payload.get("description_of_work") or payload.get("project_scope") or (item_doc.description if item_doc else "")
    invoice.project_title = payload.get("project_title") or payload.get("project_name") or ""
    invoice.project_reference = payload.get("project_reference") or ""
    invoice.project_scope = payload.get("project_scope") or ""
    invoice.contract_acknowledgement = payload.get("contract_acknowledgement") or ""
    invoice.work_ordered_by = payload.get("work_ordered_by") or ""
    invoice.discount_amount = flt(payload.get("discount_amount") or 0)
    invoice.deposit_amount = flt(payload.get("deposit_amount") or 0)
    invoice.adjustment_amount = flt(payload.get("adjustment_amount") or 0)
    _prepare_series(invoice)
    invoice.append("items", {
        "item": item_name,
        "description": payload.get("item_description") or (item_doc.description if item_doc else item_name),
        "qty": qty,
        "rate": rate,
        "amount": qty * rate,
        "vat_rate": vat_rate,
        "vat_amount": qty * rate * vat_rate / 100,
    })
    invoice.subtotal = validation.get("subtotal")
    invoice.tax_amount = validation.get("tax_total")
    invoice.total = validation.get("total")
    invoice.balance = validation.get("total")
    saved = _save(invoice)
    return _doc_dict(saved, ["name", "client", "project", "cost_center", "invoice_date", "due_date", "invoice_layout", "status", "total", "balance", "description_of_work"])



def create_sales_quotation_record(payload=None):
    payload = _payload_dict(payload)
    item_name = payload.get("item") or payload.get("product")
    item_doc = frappe.get_doc("Product", item_name) if item_name else None
    qty = flt(payload.get("qty") or 1)
    rate = flt(payload.get("rate") or (item_doc.selling_price if item_doc else 0))
    vat_rate = flt(payload.get("vat_rate") or (item_doc.vat_rate if item_doc else 15))
    subtotal = qty * rate
    tax_amount = subtotal * vat_rate / 100

    quotation = frappe.new_doc("Sales Quotation")
    quotation.client = payload.get("client")
    quotation.quotation_date = payload.get("quotation_date") or nowdate()
    quotation.valid_till = payload.get("valid_till") or add_days(quotation.quotation_date, 14)
    quotation.currency = payload.get("currency") or frappe.get_single("Daftra Settings").default_currency or "SAR"
    quotation.status = payload.get("status") or "Draft"
    quotation.notes = payload.get("notes") or ""
    _prepare_series(quotation)
    quotation.append("items", {
        "item": item_name,
        "description": payload.get("item_description") or (item_doc.description if item_doc else item_name),
        "qty": qty,
        "rate": rate,
        "amount": subtotal,
        "vat_rate": vat_rate,
        "vat_amount": tax_amount,
    })
    quotation.subtotal = subtotal
    quotation.tax_amount = tax_amount
    quotation.total = subtotal + tax_amount
    saved = _save(quotation)
    return _doc_dict(saved, ["name", "client", "quotation_date", "valid_till", "status", "total"])


def create_invoice_payment_record(payload=None):
    payload = _payload_dict(payload)
    sales_invoice = payload.get("sales_invoice")
    if not sales_invoice:
        demo = run_sales_cycle()
        sales_invoice = demo["invoice"]
    invoice_doc = frappe.get_doc("Sales Invoice", sales_invoice)

    payment = frappe.new_doc("Invoice Payment")
    payment.sales_invoice = sales_invoice
    payment.payment_date = payload.get("payment_date") or nowdate()
    payment.amount = flt(payload.get("amount") or invoice_doc.balance or invoice_doc.total or 0)
    payment.payment_method = payload.get("payment_method") or "Bank Transfer"
    payment.reference = payload.get("reference") or ""
    payment.bank_registration = payload.get("bank_registration") or frappe.db.get_value("Bank Registration", {"is_default": 1}, "name") or _demo_bank_registration().name
    payment.treasury = payload.get("treasury") or frappe.db.get_value("Treasury", {"is_active": 1}, "name") or _first_or_create("Treasury", {"treasury_name": "Main Cashbox"}, {"treasury_name": "Main Cashbox", "type": "Cash", "balance": 25000, "is_active": 1}).name
    _prepare_series(payment)
    saved = _save(payment)
    return _doc_dict(saved, ["name", "sales_invoice", "payment_date", "payment_method", "amount", "reference"])


def create_recurring_invoice_record(payload=None):
    payload = _payload_dict(payload)
    recurring = frappe.new_doc("Recurring Invoice")
    recurring.client = payload.get("client")
    recurring.frequency = payload.get("frequency") or "Monthly"
    recurring.start_date = payload.get("start_date") or nowdate()
    recurring.end_date = payload.get("end_date")
    recurring.next_invoice_date = payload.get("next_invoice_date") or recurring.start_date
    recurring.total_amount = flt(payload.get("total_amount") or 0)
    recurring.status = payload.get("status") or "Active"
    _prepare_series(recurring)
    saved = _save(recurring)
    return _doc_dict(saved, ["name", "client", "frequency", "start_date", "next_invoice_date", "total_amount", "status"])


@frappe.whitelist()
def create_project_workspace_record(payload=None):
    from daftra.api.project_api import create_project_record

    payload = _payload_dict(payload)
    return create_project_record(payload)


@frappe.whitelist()
def get_service_cycle_context(client_name=None, product_name=None, project_name=None):
    client = frappe.get_doc("Client", client_name) if client_name and frappe.db.exists("Client", client_name) else None
    product = frappe.get_doc("Product", product_name) if product_name and frappe.db.exists("Product", product_name) else None
    project = frappe.get_doc("Daftra Project", project_name) if project_name and frappe.db.exists("Daftra Project", project_name) else None
    return {
        "client": client.as_dict() if client else None,
        "product": product.as_dict() if product else None,
        "project": project.as_dict() if project else None,
        "options": _workspace_options(),
        "recommended": {
            "invoice_layout": "Materials & Services",
            "payment_method": "Bank Transfer",
            "due_date": add_days(nowdate(), 30),
            "task": product.product_name if product else "Service delivery",
            "service": product.product_name if product else "Maintenance",
            "description_of_work": (product.description or product.product_name) if product else "",
            "hourly_rate": flt(product.selling_price) if product else 250,
            "cost_rate": flt(product.purchase_price or product.selling_price) if product else 150,
        },
    }


@frappe.whitelist()
def run_service_cycle(payload=None):
    from daftra.api.project_api import create_project_record, get_project_profitability

    payload = _payload_dict(payload)
    if not payload:
        return run_demo_service_cycle()
    project_name = payload.get("project")
    project_info = None
    if payload.get("create_project") or (payload.get("project_name") and not project_name):
        project_info = create_project_record({
            "project_code": payload.get("project_code"),
            "project_name": payload.get("project_name") or payload.get("description_of_work") or "Service Project",
            "client_name": payload.get("client"),
            "project_type": payload.get("project_type") or "Service Project",
            "budget_amount": payload.get("budget_amount") or 0,
            "expected_revenue": payload.get("expected_revenue") or payload.get("rate") or 0,
            "description": payload.get("description_of_work") or payload.get("notes") or "",
            "notes": payload.get("notes") or "",
        })
        project_name = project_info["name"]
    elif project_name and frappe.db.exists("Daftra Project", project_name):
        project_info = frappe.get_doc("Daftra Project", project_name).as_dict()

    appointment = create_appointment_record({
        "client": payload.get("client"),
        "appointment_date": payload.get("appointment_date") or payload.get("booking_date") or nowdate(),
        "appointment_time": payload.get("appointment_time") or payload.get("booking_time") or "10:00:00",
        "status": payload.get("appointment_status") or "Scheduled",
        "notes": payload.get("notes") or "",
    })
    booking = create_service_booking({
        "client": payload.get("client"),
        "booking_date": payload.get("booking_date") or payload.get("appointment_date") or nowdate(),
        "booking_time": payload.get("booking_time") or payload.get("appointment_time") or "10:00:00",
        "service": payload.get("service") or payload.get("product_label") or payload.get("description_of_work") or "Maintenance",
        "status": payload.get("booking_status") or "Confirmed",
        "project": project_name,
        "notes": payload.get("notes") or "",
    })
    project_cost_center = None
    if project_name:
        project_cost_center = frappe.db.get_value("Daftra Project", project_name, "project_cost_center")
    time_entry = create_time_entry_record({
        "employee": payload.get("employee"),
        "client": payload.get("client"),
        "project": project_name,
        "cost_center": project_cost_center,
        "task": payload.get("task") or payload.get("service") or "Service delivery",
        "date": payload.get("time_entry_date") or payload.get("booking_date") or nowdate(),
        "start_time": payload.get("start_time") or payload.get("booking_time") or "09:00:00",
        "end_time": payload.get("end_time") or "11:00:00",
        "duration_hours": payload.get("duration_hours") or 2,
        "hourly_rate": payload.get("hourly_rate") or payload.get("rate") or 250,
        "cost_rate": payload.get("cost_rate") or payload.get("hourly_rate") or 150,
        "notes": payload.get("notes") or "",
    })
    invoice = create_sales_invoice_record({
        "client": payload.get("client"),
        "project": project_name,
        "cost_center": project_cost_center,
        "item": payload.get("item") or payload.get("product"),
        "qty": payload.get("qty") or 1,
        "rate": payload.get("rate") or payload.get("hourly_rate") or 250,
        "vat_rate": payload.get("vat_rate") or 15,
        "invoice_layout": payload.get("invoice_layout") or "Materials & Services",
        "due_date": payload.get("due_date") or add_days(nowdate(), 30),
        "description_of_work": payload.get("description_of_work") or payload.get("task") or payload.get("service") or "Service delivery",
        "project_title": payload.get("project_title") or (project_info.get("project_name") if project_info else ""),
        "project_reference": payload.get("project_reference") or (project_info.get("project_code") if project_info else ""),
        "project_scope": payload.get("project_scope") or payload.get("description_of_work") or "",
        "contract_acknowledgement": payload.get("contract_acknowledgement") or "",
        "notes": payload.get("notes") or "",
    })
    profitability = get_project_profitability(project_name) if project_name else None
    return {
        "appointment": appointment,
        "booking": booking,
        "project": project_info,
        "time_entry": time_entry,
        "invoice": invoice,
        "profitability": profitability,
    }


@frappe.whitelist()
def get_frontend_workspace(doctype=None, search=None, limit=20, view_key=None):
    config = _resolve_workspace_config(doctype, view_key)
    doctype = config["doctype"]
    limit = int(limit or 20)
    search = (search or "").strip()
    or_filters = []
    if search:
        meta = frappe.get_meta(doctype)
        searchable_types = {"Data", "Small Text", "Text", "Link", "Select", "Dynamic Link", "Read Only"}
        for key in config.get("list_fields", [])[:4]:
            if key == "modified":
                continue
            field = meta.get_field(key)
            if field and field.fieldtype not in searchable_types:
                continue
            or_filters.append([doctype, key, "like", f"%{search}%"])
    rows = frappe.get_all(
        doctype,
        fields=config.get("list_fields"),
        filters=config.get("filters"),
        or_filters=or_filters,
        order_by="modified desc",
        limit_page_length=limit,
    )
    records = [_record_summary(doctype, row, config) for row in rows]
    return {
        "doctype": doctype,
        "label": config.get("label") or doctype,
        "view_key": config.get("view_key"),
        "module": config.get("module"),
        "records": records,
        "create_fields": config.get("create_fields"),
        "detail_fields": config.get("detail_fields"),
        "options": _workspace_options(),
    }


@frappe.whitelist()
def get_frontend_record(doctype, name, view_key=None):
    config = _resolve_workspace_config(doctype, view_key)
    doc = frappe.get_doc(config["doctype"], name)
    payload = {field: getattr(doc, field, None) for field in config.get("detail_fields", [])}
    if config["doctype"] in {"Sales Invoice", "Sales Quotation"}:
        payload["items"] = [
            {
                "item": row.item,
                "description": row.description,
                "qty": row.qty,
                "rate": row.rate,
                "amount": row.amount,
                "vat_rate": row.vat_rate,
                "vat_amount": row.vat_amount,
            }
            for row in doc.items
        ]
    return payload


@frappe.whitelist()
def create_frontend_workspace_record(doctype, payload=None, view_key=None):
    payload = _payload_dict(payload)
    config = _resolve_workspace_config(doctype, view_key)
    doctype = config["doctype"]
    if doctype == "Client":
        return create_client_record(payload)
    if doctype == "Supplier":
        return create_supplier_record(payload)
    if doctype == "Purchase Request":
        return create_purchase_request_record(payload)
    if doctype == "Purchase Quotation":
        return create_purchase_quotation_record(payload)
    if doctype == "Purchase Order":
        return create_purchase_order_record(payload)
    if doctype == "Purchase Invoice":
        return create_purchase_invoice_record(payload)
    if doctype == "Supplier Payment":
        return create_supplier_payment_record(payload)
    if doctype == "Product":
        return create_product_record(payload)
    if doctype == "Warehouse":
        return create_warehouse_record(payload)
    if doctype == "Price List":
        return create_price_list_record(payload)
    if doctype == "Price List Rule":
        return create_price_list_rule_record(payload)
    if doctype == "Stock Entry":
        return create_stock_entry_record(payload)
    if doctype == "Stocktaking":
        return create_stocktaking_record(payload)
    if doctype == "Requisition":
        return create_requisition_record(payload)
    if doctype == "Daftra Project":
        return create_project_workspace_record(payload)
    if doctype == "Client Contact":
        return create_client_contact_record(payload)
    if doctype == "Appointment":
        return create_appointment_record(payload)
    if doctype == "CRM Deal":
        return create_crm_deal_record(payload)
    if doctype == "Insurance Agent":
        return create_insurance_agent_record(payload)
    if doctype == "Credit Type":
        return create_credit_type_record(payload)
    if doctype == "Credit Package":
        return create_credit_package_record(payload)
    if doctype == "Credit Charge":
        return create_credit_charge_record(payload)
    if doctype == "Credit Usage":
        return create_credit_usage_record(payload)
    if doctype == "Booking":
        return create_service_booking(payload)
    if doctype == "Time Entry":
        return create_time_entry_record(payload)
    if doctype == "Sales Invoice":
        if view_key == "credit_notes":
            payload["invoice_type"] = "Credit Note"
        elif view_key == "refund_receipts":
            payload["invoice_type"] = "Refund"
        else:
            payload.setdefault("invoice_type", "Normal")
        return create_sales_invoice_record(payload)
    if doctype == "Sales Quotation":
        return create_sales_quotation_record(payload)
    if doctype == "Invoice Payment":
        return create_invoice_payment_record(payload)
    if doctype == "Recurring Invoice":
        return create_recurring_invoice_record(payload)
    frappe.throw(_("Unsupported workspace doctype"))


@frappe.whitelist()
def get_low_stock(limit=8):
    limit = int(limit or 8)
    rows = frappe.get_all(
        "Product",
        fields=["name", "product_code", "product_name", "current_stock", "minimum_stock", "status"],
        filters={"minimum_stock": [">", 0]},
        order_by="current_stock asc",
    )
    return [row for row in rows if flt(row.current_stock) <= flt(row.minimum_stock)][:limit]


@frappe.whitelist()
def get_recent_activity(limit=10):
    limit = int(limit or 10)
    doctypes = ["Sales Invoice", "Sales Quotation", "Purchase Invoice", "Client", "Product", "Invoice Payment", "Booking", "Time Entry"]
    rows = []
    for doctype in doctypes:
        if not frappe.db.exists("DocType", doctype):
            continue
        for row in frappe.get_all(doctype, fields=["name", "modified", "owner"], order_by="modified desc", limit_page_length=3):
            row["doctype"] = doctype
            rows.append(row)
    rows.sort(key=lambda r: r.modified, reverse=True)
    return rows[:limit]


@frappe.whitelist()
def seed_demo_data():
    _require_manager()
    settings = frappe.get_single("Daftra Settings")
    settings.company_name = settings.company_name or "Galaxy Labs Daftra"
    settings.default_currency = settings.default_currency or "SAR"
    settings.vat_number = settings.vat_number or "300000000000003"
    settings.enable_zatca = 1
    for field in [
        "enable_sales_module", "enable_clients_module", "enable_inventory_module", "enable_purchases_module",
        "enable_accounting_module", "enable_hr_module", "enable_pos_module", "enable_bookings_module",
        "enable_time_tracking_module", "enable_tax_module",
    ]:
        setattr(settings, field, 1)
    settings.save(ignore_permissions=True)

    client = _demo_client()
    supplier = _demo_supplier()
    product = _demo_product()
    warehouse = _demo_warehouse()
    tax = _demo_tax()

    _first_or_create("Treasury", {"treasury_name": "Main Cashbox"}, {"treasury_name": "Main Cashbox", "type": "Cash", "balance": 25000, "is_active": 1})
    bank = _demo_bank_registration()
    _first_or_create("Employee", {"employee_id": "EMP-DEMO-001"}, {"employee_name": "Aisha Demo", "employee_id": "EMP-DEMO-001", "email": "aisha@example.com", "hire_date": nowdate(), "basic_salary": 4500, "status": "Active"})
    _first_or_create("Shift", {"shift_name": "Morning"}, {"shift_name": "Morning", "start_time": "08:00:00", "end_time": "16:00:00", "late_grace_period": 15})
    _first_or_create("Price List", {"price_list_name": "Standard"}, {"price_list_name": "Standard", "currency": "SAR", "is_default": 1})

    return {"client": client.name, "supplier": supplier.name, "product": product.name, "warehouse": warehouse.name, "tax": tax.name, "bank_registration": bank.name}


@frappe.whitelist()
def run_sales_cycle():
    _require_manager()
    seed_demo_data()
    client = _demo_client()
    product = _demo_product()
    today = nowdate()

    quotation = frappe.new_doc("Sales Quotation")
    quotation.client = client.name
    quotation.quotation_date = today
    quotation.valid_till = add_days(today, 14)
    quotation.currency = "SAR"
    quotation.status = "Accepted"
    quotation.append("items", {"item": product.name, "description": product.product_name, "qty": 2, "rate": 250})
    _prepare_series(quotation)
    quotation = _save(quotation)

    invoice = frappe.new_doc("Sales Invoice")
    invoice.client = client.name
    invoice.invoice_date = today
    invoice.due_date = add_days(today, 30)
    invoice.currency = "SAR"
    invoice.invoice_layout = "TAX Invoice"
    invoice.delivery_method = "Print (Offline)"
    invoice.payment_method = "Bank Transfer"
    invoice.payment_terms_days = 30
    invoice.type_of_service = "Maintenance"
    invoice.description_of_work = "Demo maintenance package with VAT"
    invoice.append("items", {"item": product.name, "description": product.product_name, "qty": 2, "rate": 250, "vat_rate": 15})
    _prepare_series(invoice)
    invoice = _save(invoice, submit=True)

    payment = frappe.new_doc("Invoice Payment")
    payment.sales_invoice = invoice.name
    payment.payment_date = today
    payment.amount = invoice.total
    payment.payment_method = "Bank Transfer"
    payment.bank_registration = _demo_bank_registration().name
    payment.reference = "DEMO-SALES-CYCLE"
    _prepare_series(payment)
    payment = _save(payment)

    return {"quotation": quotation.name, "invoice": invoice.name, "payment": payment.name, "total": invoice.total}


@frappe.whitelist()
def run_purchase_cycle():
    _require_manager()
    seed_demo_data()
    supplier = _demo_supplier()
    product = _demo_product()
    today = nowdate()

    invoice = frappe.new_doc("Purchase Invoice")
    invoice.supplier = supplier.name
    invoice.invoice_date = today
    invoice.due_date = add_days(today, 30)
    invoice.invoice_type = "Purchase"
    invoice.status = "Submitted"
    invoice.payment_terms_days = 30
    invoice.append("items", {"product": product.name, "description": product.product_name, "qty": 5, "rate": 120, "vat_rate": 15})
    _prepare_series(invoice)
    invoice = _save(invoice, submit=True)

    payment = frappe.new_doc("Supplier Payment")
    payment.purchase_invoice = invoice.name
    payment.payment_date = today
    payment.amount = invoice.total
    payment.payment_method = "Bank Transfer"
    payment.bank_registration = _demo_bank_registration().name
    _prepare_series(payment)
    payment = _save(payment)

    return {"purchase_invoice": invoice.name, "supplier_payment": payment.name, "total": invoice.total}


def run_demo_service_cycle():
    _require_manager()
    settings = frappe.get_single("Daftra Settings")
    settings.business_type = "Services"
    settings.frontend_setup_completed = 1
    settings.enable_sales_module = 1
    settings.enable_clients_module = 1
    settings.enable_inventory_module = 1
    settings.enable_purchases_module = 1
    settings.enable_accounting_module = 1
    settings.enable_hr_module = 1
    settings.enable_pos_module = 1
    settings.enable_bookings_module = 1
    settings.enable_time_tracking_module = 1
    settings.enable_tax_module = 1
    settings.enable_zatca = 1
    settings.save(ignore_permissions=True)

    client = _demo_client()
    product = _demo_product()
    booking = create_service_booking({"client": client.name, "service": product.product_name})
    time_entry = create_time_entry_record({"client": client.name, "task": product.product_name, "duration_hours": 2, "hourly_rate": product.selling_price, "billable_amount": flt(product.selling_price) * 2})

    today = nowdate()
    invoice = frappe.new_doc("Sales Invoice")
    invoice.client = client.name
    invoice.invoice_date = today
    invoice.due_date = add_days(today, client.credit_period or 30)
    invoice.currency = settings.default_currency or "SAR"
    invoice.invoice_layout = "Materials & Services"
    invoice.delivery_method = "Print (Offline)"
    invoice.payment_method = "Bank Transfer"
    invoice.payment_terms_days = client.credit_period or 30
    invoice.type_of_service = "Maintenance"
    invoice.description_of_work = f"{product.product_name} for {client.business_name or client.first_name}"
    invoice.append("items", {
        "item": product.name,
        "description": product.product_name,
        "qty": flt(time_entry["duration_hours"] or 2),
        "rate": flt(product.selling_price),
        "vat_rate": flt(product.vat_rate or 15),
    })
    _prepare_series(invoice)
    invoice = _save(invoice, submit=True)

    payment = frappe.new_doc("Invoice Payment")
    payment.sales_invoice = invoice.name
    payment.payment_date = today
    payment.amount = invoice.total
    payment.payment_method = "Bank Transfer"
    payment.bank_registration = _demo_bank_registration().name
    payment.reference = "DEMO-SERVICE-CYCLE"
    _prepare_series(payment)
    payment = _save(payment)

    return {
        "client": client.name,
        "product": product.name,
        "booking": booking["name"],
        "time_entry": time_entry["name"],
        "invoice": invoice.name,
        "payment": payment.name,
        "total": invoice.total,
    }


@frappe.whitelist()
def validate_business_cycle():
    checks = []
    for doctype in ["Client", "Product", "Supplier", "Sales Invoice", "Invoice Payment", "Purchase Invoice", "Supplier Payment"]:
        count = frappe.db.count(doctype)
        checks.append({"doctype": doctype, "count": count, "ok": count > 0})
    checks.append({"doctype": "Low Stock Panel", "count": len(get_low_stock()), "ok": True})
    checks.append({"doctype": "Service Setup", "count": 1 if frappe.get_single("Daftra Settings").business_type == "Services" else 0, "ok": True})
    return {"ok": all(row["ok"] for row in checks), "checks": checks}


PRINT_TEMPLATES = [
    {"key": "default_invoice", "label": "Default Invoice", "doctype": "Sales Invoice", "description": "Full invoice with company header and signatures", "defaults": {"header": 1, "party": 1, "vat": 1, "qr": 0, "notes": 1, "signature": 1}},
    {"key": "tax_invoice", "label": "TAX Invoice", "doctype": "Sales Invoice", "description": "ZATCA-ready VAT invoice with QR area", "defaults": {"header": 1, "party": 1, "vat": 1, "qr": 1, "notes": 1, "signature": 1}},
    {"key": "receipt", "label": "Receipt 80mm", "doctype": "Sales Invoice", "description": "Compact thermal receipt", "defaults": {"header": 1, "party": 0, "vat": 1, "qr": 0, "notes": 0, "signature": 0}},
    {"key": "materials_services", "label": "Materials & Services", "doctype": "Sales Invoice", "description": "Work-focused project invoice", "defaults": {"header": 1, "party": 1, "vat": 1, "qr": 0, "notes": 1, "signature": 1}},
    {"key": "quotation", "label": "Quotation", "doctype": "Sales Quotation", "description": "Customer quotation and acceptance", "defaults": {"header": 1, "party": 1, "vat": 0, "qr": 0, "notes": 1, "signature": 1}},
    {"key": "purchase_order", "label": "Purchase Order", "doctype": "Purchase Order", "description": "Supplier order and approval", "defaults": {"header": 1, "party": 1, "vat": 1, "qr": 0, "notes": 1, "signature": 1}},
    {"key": "timesheet", "label": "Timesheet", "doctype": "Time Entry", "description": "Hours, rates and billable work", "defaults": {"header": 1, "party": 1, "vat": 0, "qr": 0, "notes": 1, "signature": 1}},
]

PRINT_DOCTYPES = {row["doctype"] for row in PRINT_TEMPLATES}


def _print_value(value):
    return html.escape(str(value if value not in (None, "") else "-"))


def _print_options(options):
    if isinstance(options, str):
        options = json.loads(options or "{}")
    return {key: bool(int(value)) if isinstance(value, str) and value.isdigit() else bool(value) for key, value in (options or {}).items()}


@frappe.whitelist()
def get_print_studio():
    from daftra.api.dashboard_api import get_document_catalog

    templates = []
    for template in PRINT_TEMPLATES:
        row = dict(template)
        row["records"] = frappe.get_all(template["doctype"], fields=["name", "modified"], order_by="modified desc", limit_page_length=20)
        templates.append(row)
    return {"templates": templates, "documents": get_document_catalog()}


@frappe.whitelist()
def get_print_preview(doctype, name, template_key, options=None):
    if doctype not in PRINT_DOCTYPES:
        frappe.throw(_("Unsupported print document"))
    template = next((row for row in PRINT_TEMPLATES if row["key"] == template_key and row["doctype"] == doctype), None)
    if not template:
        frappe.throw(_("Invalid print template"))
    doc = frappe.get_doc(doctype, name)
    if not frappe.has_permission(doctype, "read", doc):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    selected = dict(template["defaults"])
    selected.update(_print_options(options))
    settings = frappe.get_single("Daftra Settings")
    currency = getattr(doc, "currency", None) or settings.default_currency or "SAR"
    party_label = "Client" if hasattr(doc, "client") else "Supplier" if hasattr(doc, "supplier") else "Employee"
    party = getattr(doc, "client", None) or getattr(doc, "supplier", None) or getattr(doc, "employee", None) or "-"
    date = getattr(doc, "invoice_date", None) or getattr(doc, "quotation_date", None) or getattr(doc, "order_date", None) or getattr(doc, "date", None) or "-"
    items = list(getattr(doc, "items", None) or [])
    if not items and doctype == "Time Entry":
        items = [frappe._dict({"description": doc.task, "qty": doc.duration_hours, "rate": doc.hourly_rate, "amount": doc.billable_amount, "vat_amount": 0})]
    rows = "".join(
        f"<tr><td>{index}</td><td>{_print_value(getattr(item, 'description', None) or getattr(item, 'item', None) or getattr(item, 'product', None))}</td><td>{_print_value(getattr(item, 'qty', 1))}</td><td>{_print_value(getattr(item, 'rate', 0))}</td><td>{_print_value(getattr(item, 'amount', 0))}</td></tr>"
        for index, item in enumerate(items, 1)
    )
    subtotal = getattr(doc, "subtotal", None) or sum(flt(getattr(item, "amount", 0)) for item in items)
    tax = getattr(doc, "tax_amount", None) or sum(flt(getattr(item, "vat_amount", 0)) for item in items)
    total = getattr(doc, "total", None) or getattr(doc, "billable_amount", None) or subtotal + tax
    width = "80mm" if template_key == "receipt" else "210mm"
    header = f"<header><h1>{_print_value(settings.company_name or 'Daftra')}</h1><p>VAT: {_print_value(settings.vat_number)} | CR: {_print_value(settings.cr_number)}</p></header>" if selected.get("header") else ""
    party_html = f"<section class=party><b>{party_label}</b><span>{_print_value(party)}</span><b>Date</b><span>{_print_value(date)}</span><b>Document</b><span>{_print_value(doc.name)}</span></section>" if selected.get("party") else ""
    project_html = ""
    if doctype == "Sales Invoice" and any(getattr(doc, field, None) for field in ["project_title", "project_reference", "project_location", "project_scope", "contract_acknowledgement"]):
        project_html = f"<section class=project><h3>{_print_value(getattr(doc, 'project_title', None) or 'Project Details')}</h3><div><b>Reference</b><span>{_print_value(getattr(doc, 'project_reference', None))}</span><b>Location</b><span>{_print_value(getattr(doc, 'project_location', None))}</span></div><p>{_print_value(getattr(doc, 'project_scope', None))}</p><small>{_print_value(getattr(doc, 'contract_acknowledgement', None))}</small></section>"
    vat_html = f"<div><span>VAT</span><b>{_print_value(tax)} {currency}</b></div>" if selected.get("vat") else ""
    qr_html = "<div class=qr><span>ZATCA</span><b>QR</b></div>" if selected.get("qr") else ""
    notes = f"<section class=notes><b>Notes</b><p>{_print_value(getattr(doc, 'notes', None))}</p></section>" if selected.get("notes") else ""
    signature = "<section class=sign><span>Prepared by</span><span>Approved by</span><span>Received by</span></section>" if selected.get("signature") else ""
    style = f"@page{{size:{width} auto;margin:10mm}}*{{box-sizing:border-box}}body{{font-family:Arial,sans-serif;color:#17211f;width:{width};margin:0 auto;padding:10mm;font-size:12px}}header{{border-bottom:3px solid #176b57;padding-bottom:12px;margin-bottom:16px}}h1{{margin:0;font-size:24px}}.title{{display:flex;justify-content:space-between;align-items:end;margin:16px 0}}.party{{display:grid;grid-template-columns:100px 1fr;gap:6px 14px;background:#f2f5f2;padding:12px;margin-bottom:14px}}table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #dbe2de;padding:8px;text-align:left}}th{{background:#123f35;color:white}}.summary{{margin:14px 0 14px auto;width:260px}}.summary div{{display:flex;justify-content:space-between;padding:5px 0}}.total{{font-size:16px;border-top:2px solid #17211f}}.qr{{width:88px;height:88px;border:2px dashed #17211f;display:grid;place-content:center;text-align:center;margin:15px 0 15px auto}}.notes{{border-top:1px solid #dbe2de;padding-top:10px}}.sign{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:45px}}.sign span{{border-top:1px solid #17211f;padding-top:6px;text-align:center}}@media print{{body{{padding:0}}}}"
    label = template.get("label")
    body = f"<!doctype html><html><head><meta charset=utf-8><style>{style}</style></head><body>{header}<div class=title><div><small>{_print_value(label)}</small><h2>{_print_value(doctype)}</h2></div><b>{_print_value(doc.name)}</b></div>{party_html}{project_html}<table><thead><tr><th>#</th><th>Description</th><th>Qty</th><th>Rate</th><th>Amount</th></tr></thead><tbody>{rows or '<tr><td colspan=5>No items</td></tr>'}</tbody></table><section class=summary><div><span>Subtotal</span><b>{_print_value(subtotal)} {currency}</b></div>{vat_html}<div class=total><span>Total</span><b>{_print_value(total)} {currency}</b></div></section>{qr_html}{notes}{signature}</body></html>"
    return {"html": body, "title": f"{label} - {doc.name}"}
