import html
import json

import frappe
from frappe import _
from frappe.utils import add_days, flt, nowdate

MODULE_MAP = {
    "Sales": ["Sales Invoice", "Sales Quotation", "Invoice Payment", "Recurring Invoice", "Installment Agreement", "Sales Commission"],
    "Clients": ["Client", "Client Contact", "Appointment", "CRM Deal", "Credit Charge", "Credit Usage", "Insurance Agent"],
    "Inventory": ["Product", "Warehouse", "Stock Entry", "Stocktaking", "Price List", "Price List Rule"],
    "Purchases": ["Supplier", "Purchase Request", "Purchase Quotation", "Purchase Order", "Purchase Invoice", "Supplier Payment"],
    "Accounting": ["Account", "Cost Center", "Journal Entry", "Expense", "Income", "Treasury", "Bank Registration", "Asset"],
    "HR": ["Employee", "Employee Role", "Shift", "Employee Attendance", "Employee Contract", "Payroll Entry", "Leave Request"],
    "POS": ["POS Session"],
    "Bookings": ["Booking"],
    "Time Tracking": ["Time Entry"],
    "Tax": ["Tax Setting"],
    "Settings": ["Daftra Settings"],
}

SCENARIOS = [
    {"key": "lead_to_cash", "label": "Lead to cash", "steps": ["Client", "Quotation", "Invoice", "Payment", "Receipt"]},
    {"key": "procure_to_stock", "label": "Procure to stock", "steps": ["Supplier", "Purchase Invoice", "Stock Increase", "Supplier Payment"]},
    {"key": "service_job", "label": "Service job", "steps": ["Booking", "Time Entry", "Invoice", "ZATCA QR"]},
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
    "Time Entry": "TIM-.YYYY.-",
    "Employee": "EMP-.YYYY.-",
    "Shift": "SHF-.YYYY.-",
    "Journal Entry": "JRN-.YYYY.-",
    "Expense": "EXP-.YYYY.-",
    "Income": "INC-.YYYY.-",
    "Treasury": "TRE-.YYYY.-",
    "Bank Registration": "BNK-.YYYY.-",
    "Asset": "AST-.YYYY.-",
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
    client.city = payload.get("city") or "Riyadh"
    client.country = payload.get("country") or "Saudi Arabia"
    client.tax_id = payload.get("tax_id") or ""
    client.cr_number = payload.get("cr_number") or ""
    client.credit_limit = payload.get("credit_limit") or 0
    client.credit_period = payload.get("credit_period") or 30
    client.notes = payload.get("notes") or ""
    _prepare_series(client)
    saved = _save(client)
    return _doc_dict(saved, ["name", "client_type", "business_name", "first_name", "phone", "mobile", "email", "city", "country", "tax_id", "credit_period"])


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
    booking.notes = payload.get("notes") or "Booked from Daftra service flow"
    _prepare_series(booking)
    saved = _save(booking)
    return _doc_dict(saved, ["name", "client", "booking_date", "booking_time", "service", "status"])


@frappe.whitelist()
def create_time_entry_record(payload=None):
    payload = _payload_dict(payload)
    time_entry = frappe.new_doc("Time Entry")
    time_entry.employee = payload.get("employee")
    time_entry.client = payload.get("client")
    time_entry.task = payload.get("task") or "Service delivery"
    time_entry.date = payload.get("date") or nowdate()
    time_entry.start_time = payload.get("start_time") or "09:00:00"
    time_entry.end_time = payload.get("end_time") or "11:00:00"
    time_entry.duration_hours = flt(payload.get("duration_hours") or 2)
    time_entry.hourly_rate = flt(payload.get("hourly_rate") or 250)
    time_entry.billable_amount = flt(payload.get("billable_amount") or time_entry.duration_hours * time_entry.hourly_rate)
    time_entry.is_billed = int(payload.get("is_billed") or 0)
    time_entry.notes = payload.get("notes") or "Demo billable time entry"
    _prepare_series(time_entry)
    saved = _save(time_entry)
    return _doc_dict(saved, ["name", "client", "task", "date", "duration_hours", "hourly_rate", "billable_amount", "is_billed"])


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
        "detail_fields": ["name", "client_type", "business_name", "first_name", "last_name", "phone", "mobile", "email", "city", "country", "tax_id", "credit_period", "notes"],
        "create_fields": [
            {"fieldname": "business_name", "label": "Business Name", "type": "Data", "required": 1},
            {"fieldname": "first_name", "label": "Primary Contact", "type": "Data"},
            {"fieldname": "email", "label": "Email", "type": "Data"},
            {"fieldname": "phone", "label": "Phone", "type": "Data"},
            {"fieldname": "city", "label": "City", "type": "Data"},
            {"fieldname": "tax_id", "label": "VAT / Tax ID", "type": "Data"},
            {"fieldname": "credit_period", "label": "Credit Period", "type": "Int"},
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
        "detail_fields": ["name", "employee", "client", "task", "date", "start_time", "end_time", "duration_hours", "hourly_rate", "billable_amount", "notes"],
        "create_fields": [
            {"fieldname": "client", "label": "Client", "type": "Link", "options_key": "clients"},
            {"fieldname": "task", "label": "Task", "type": "Data", "required": 1},
            {"fieldname": "date", "label": "Date", "type": "Date", "required": 1},
            {"fieldname": "duration_hours", "label": "Duration Hours", "type": "Float"},
            {"fieldname": "hourly_rate", "label": "Hourly Rate", "type": "Currency"},
            {"fieldname": "notes", "label": "Notes", "type": "Text"},
        ],
    },
    "Sales Invoice": {
        "module": "Sales",
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
}


def _resolve_workspace_config(doctype):
    config = WORKSPACE_CONFIG.get(doctype)
    if not config:
        frappe.throw(_("Unsupported workspace doctype"))
    return config


def _workspace_options():
    return {
        "clients": frappe.get_all("Client", fields=["name", "business_name", "first_name", "last_name", "tax_id"], order_by="modified desc", limit_page_length=100),
        "products": frappe.get_all("Product", fields=["name", "product_code", "product_name", "product_type", "selling_price", "vat_rate"], order_by="modified desc", limit_page_length=100),
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
        "description_of_work": payload.get("description_of_work") or payload.get("project_scope") or payload.get("notes"),
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
    invoice.description_of_work = payload.get("description_of_work") or payload.get("project_scope") or (item_doc.description if item_doc else "")
    invoice.project_title = payload.get("project_title") or ""
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
    return _doc_dict(saved, ["name", "client", "invoice_date", "due_date", "invoice_layout", "status", "total", "balance", "description_of_work"])


@frappe.whitelist()
def get_frontend_workspace(doctype=None, search=None, limit=20):
    doctype = doctype or "Client"
    config = _resolve_workspace_config(doctype)
    limit = int(limit or 20)
    search = (search or "").strip()
    or_filters = []
    if search:
        for key in config.get("list_fields", [])[:4]:
            if key != "modified":
                or_filters.append([doctype, key, "like", f"%{search}%"])
    rows = frappe.get_all(doctype, fields=config.get("list_fields"), or_filters=or_filters, order_by="modified desc", limit_page_length=limit)
    records = [_record_summary(doctype, row, config) for row in rows]
    return {
        "doctype": doctype,
        "module": config.get("module"),
        "records": records,
        "create_fields": config.get("create_fields"),
        "detail_fields": config.get("detail_fields"),
        "options": _workspace_options(),
    }


@frappe.whitelist()
def get_frontend_record(doctype, name):
    config = _resolve_workspace_config(doctype)
    doc = frappe.get_doc(doctype, name)
    payload = {field: getattr(doc, field, None) for field in config.get("detail_fields", [])}
    if doctype == "Sales Invoice":
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
def create_frontend_workspace_record(doctype, payload=None):
    payload = _payload_dict(payload)
    if doctype == "Client":
        return create_client_record(payload)
    if doctype == "Product":
        return create_product_record(payload)
    if doctype == "Booking":
        return create_service_booking(payload)
    if doctype == "Time Entry":
        return create_time_entry_record(payload)
    if doctype == "Sales Invoice":
        return create_sales_invoice_record(payload)
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


@frappe.whitelist()
def run_service_cycle():
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
