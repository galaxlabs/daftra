import frappe
from frappe import _
from frappe.utils import add_days, flt, nowdate

MODULE_MAP = {
    "Sales": ["Sales Invoice", "Sales Quotation", "Invoice Payment", "Recurring Invoice", "Installment Agreement", "Sales Commission"],
    "Clients": ["Client", "Client Contact", "Appointment", "CRM Deal", "Credit Charge", "Credit Usage", "Insurance Agent"],
    "Inventory": ["Product", "Warehouse", "Stock Entry", "Stocktaking", "Price List", "Price List Rule"],
    "Purchases": ["Supplier", "Purchase Request", "Purchase Quotation", "Purchase Order", "Purchase Invoice", "Supplier Payment"],
    "Accounting": ["Account", "Cost Center", "Journal Entry", "Expense", "Income", "Treasury", "Asset"],
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


def _save(doc, submit=False):
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    if submit and getattr(doc, "docstatus", 0) == 0:
        doc.submit()
    return doc


def _first_or_create(doctype, filters, values):
    name = frappe.db.get_value(doctype, filters, "name")
    if name:
        return frappe.get_doc(doctype, name)
    doc = frappe.new_doc(doctype)
    doc.update(values)
    return _save(doc)


def _demo_client():
    return _first_or_create("Client", {"business_name": "Daftra Demo Trading"}, {
        "client_type": "Business",
        "business_name": "Daftra Demo Trading",
        "email": "demo.client@example.com",
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
        "supplier_type": "Business",
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
        "tax_type": "Sales",
        "is_default": 1,
        "is_zatca_compliant": 1,
        "is_active": 1,
    })


@frappe.whitelist()
def get_frontend_boot():
    from daftra.api.dashboard_api import get_dashboard_stats, get_enabled_modules

    return {
        "stats": get_dashboard_stats(),
        "enabled_modules": get_enabled_modules(),
        "modules": MODULE_MAP,
        "scenarios": SCENARIOS,
        "low_stock": get_low_stock(),
        "recent_activity": get_recent_activity(),
    }


@frappe.whitelist()
def get_low_stock(limit=8):
    limit = int(limit or 8)
    return frappe.get_all(
        "Product",
        fields=["name", "product_code", "product_name", "current_stock", "minimum_stock", "status"],
        filters=[["minimum_stock", ">", 0], ["current_stock", "<=", "minimum_stock"]],
        order_by="current_stock asc",
        limit_page_length=limit,
    )


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
    _first_or_create("Employee", {"employee_id": "EMP-DEMO-001"}, {"employee_name": "Aisha Demo", "employee_id": "EMP-DEMO-001", "email": "aisha@example.com", "role": "Sales", "hire_date": nowdate(), "basic_salary": 4500, "status": "Active"})
    _first_or_create("Shift", {"shift_name": "Morning"}, {"shift_name": "Morning", "start_time": "08:00:00", "end_time": "16:00:00", "late_grace_period": 15})
    _first_or_create("Price List", {"price_list_name": "Standard"}, {"price_list_name": "Standard", "currency": "SAR", "is_default": 1})

    return {"client": client.name, "supplier": supplier.name, "product": product.name, "warehouse": warehouse.name, "tax": tax.name}


@frappe.whitelist()
def run_sales_cycle():
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
    _save(quotation)

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
    _save(invoice, submit=True)

    payment = frappe.new_doc("Invoice Payment")
    payment.sales_invoice = invoice.name
    payment.payment_date = today
    payment.amount = invoice.total
    payment.payment_method = "Bank Transfer"
    payment.reference = "DEMO-SALES-CYCLE"
    _save(payment, submit=True)

    return {"quotation": quotation.name, "invoice": invoice.name, "payment": payment.name, "total": invoice.total}


@frappe.whitelist()
def run_purchase_cycle():
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
    _save(invoice, submit=True)

    payment = frappe.new_doc("Supplier Payment")
    payment.purchase_invoice = invoice.name
    payment.payment_date = today
    payment.amount = invoice.total
    payment.payment_method = "Bank Transfer"
    _save(payment, submit=True)

    return {"purchase_invoice": invoice.name, "supplier_payment": payment.name, "total": invoice.total}


@frappe.whitelist()
def validate_business_cycle():
    checks = []
    for doctype in ["Client", "Product", "Supplier", "Sales Invoice", "Invoice Payment", "Purchase Invoice", "Supplier Payment"]:
        checks.append({"doctype": doctype, "count": frappe.db.count(doctype), "ok": frappe.db.count(doctype) > 0})
    checks.append({"doctype": "Low Stock Panel", "count": len(get_low_stock()), "ok": True})
    return {"ok": all(row["ok"] for row in checks), "checks": checks}
