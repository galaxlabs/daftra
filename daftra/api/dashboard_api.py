import json

import frappe
from frappe import _

from daftra.api import reporting_api

MODULE_FIELDS = {
    "Sales": "enable_sales_module",
    "Clients": "enable_clients_module",
    "Inventory": "enable_inventory_module",
    "Purchases": "enable_purchases_module",
    "Accounting": "enable_accounting_module",
    "HR": "enable_hr_module",
    "POS": "enable_pos_module",
    "Bookings": "enable_bookings_module",
    "Time Tracking": "enable_time_tracking_module",
    "Tax": "enable_tax_module",
}


LANGUAGE_MAP = {
    "en": "English",
    "ar": "Arabic",
    "English": "English",
    "Arabic": "Arabic",
}
SETUP_FIELDS = [
    "business_type",
    "business_industry",
    "default_language",
    "frontend_setup_completed",
    "company_name",
    "default_currency",
    "company_logo",
    "vat_number",
    "cr_number",
    "enable_zatca",
]

BUSINESS_TYPES = [
    {"value": "Services", "label": _("Services")},
    {"value": "Trading", "label": _("Trading")},
    {"value": "Retail", "label": _("Retail")},
    {"value": "Wholesale", "label": _("Wholesale")},
    {"value": "Mixed", "label": _("Mixed")},
]

BUSINESS_INDUSTRIES = {
    "Services": [
        {"value": "General Services", "label": _("General Services")},
        {"value": "Maintenance & Contracting", "label": _("Maintenance & Contracting")},
        {"value": "Professional Services", "label": _("Professional Services")},
        {"value": "Consulting", "label": _("Consulting")},
        {"value": "Technology Services", "label": _("Technology Services")},
        {"value": "Healthcare Services", "label": _("Healthcare Services")},
        {"value": "Education & Training", "label": _("Education & Training")},
        {"value": "Construction", "label": _("Construction")},
    ],
    "Trading": [
        {"value": "Trading", "label": _("Trading")},
        {"value": "Wholesale Distribution", "label": _("Wholesale Distribution")},
        {"value": "E-Commerce", "label": _("E-Commerce")},
    ],
    "Retail": [
        {"value": "Retail Store", "label": _("Retail Store")},
        {"value": "E-Commerce", "label": _("E-Commerce")},
    ],
    "Wholesale": [
        {"value": "Wholesale Distribution", "label": _("Wholesale Distribution")},
        {"value": "Manufacturing", "label": _("Manufacturing")},
    ],
    "Mixed": [
        {"value": "Mixed Operations", "label": _("Mixed Operations")},
        {"value": "General Services", "label": _("General Services")},
        {"value": "Trading", "label": _("Trading")},
    ],
}

DOCUMENT_CATALOG = {
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

PRINT_TEMPLATE_MATRIX = {
    "Sales Invoice": ["Default Invoice", "TAX Invoice", "Receipt", "Materials & Services"],
    "Sales Quotation": ["Quotation"],
    "Purchase Order": ["Purchase Order"],
    "Purchase Invoice": ["Default Invoice", "TAX Invoice"],
    "Invoice Payment": ["Receipt"],
    "Supplier Payment": ["Receipt"],
    "Time Entry": ["Timesheet"],
    "Booking": ["Quotation"],
    "Bank Registration": [],
}


def get_module_status(module_name):
    """Check if a Daftra module is enabled."""
    settings = frappe.get_single("Daftra Settings")
    field = MODULE_FIELDS.get(module_name)
    if not field:
        field = "enable_" + frappe.scrub(module_name).replace("daftra_", "") + "_module"
    return getattr(settings, field, 1)


def get_enabled_modules():
    """Get all enabled Daftra modules."""
    settings = frappe.get_single("Daftra Settings")
    return {module: getattr(settings, field, 1) for module, field in MODULE_FIELDS.items()}


def get_setup_state():
    settings = frappe.get_single("Daftra Settings")
    current_type = getattr(settings, "business_type", None) or "Services"
    return {
        field: getattr(settings, field, None) for field in SETUP_FIELDS
    } | {
        "business_types": BUSINESS_TYPES,
        "business_industries": BUSINESS_INDUSTRIES,
        "industry_options": BUSINESS_INDUSTRIES.get(current_type, BUSINESS_INDUSTRIES["Services"]),
        "languages": [
            {"value": "en", "label": _("English")},
            {"value": "ar", "label": _("Arabic")},
        ],
        "currencies": ["SAR", "AED", "USD", "EUR", "GBP", "PKR"],
    }


@frappe.whitelist()
def save_frontend_setup(payload=None):
    settings = frappe.get_single("Daftra Settings")
    if isinstance(payload, str):
        payload = json.loads(payload or "{}")
    payload = payload or {}
    business_type = payload.get("business_type") or "Services"
    if business_type not in {item["value"] for item in BUSINESS_TYPES}:
        frappe.throw(_("Unsupported business type"))
    business_industry = payload.get("business_industry")
    if business_industry and business_industry not in {item["value"] for item in BUSINESS_INDUSTRIES.get(business_type, [])}:
        frappe.throw(_("Unsupported business industry"))
    for field in SETUP_FIELDS:
        if field in payload and payload[field] is not None:
            value = payload[field]
            if field == "default_language":
                value = LANGUAGE_MAP.get(value, value)
            setattr(settings, field, value)
    settings.business_type = business_type
    if business_industry:
        settings.business_industry = business_industry
    settings.frontend_setup_completed = 1
    settings.save(ignore_permissions=True)
    frappe.db.commit()
    return get_setup_state()


@frappe.whitelist()
def get_dashboard_stats():
    """Get dashboard statistics."""
    stats = {}

    if get_module_status("Sales"):
        stats["total_invoices"] = frappe.db.count("Sales Invoice")
        stats["total_invoice_amount"] = frappe.db.sql("""
            SELECT COALESCE(SUM(total), 0) FROM `tabSales Invoice` WHERE docstatus = 1
        """)[0][0] or 0
        stats["unpaid_invoices"] = frappe.db.count("Sales Invoice", {"status": ["in", ["Unpaid", "Overdue"]]})
        stats["last_7_days_sales"] = frappe.db.sql("""
            SELECT COALESCE(SUM(total), 0)
            FROM `tabSales Invoice`
            WHERE docstatus = 1 AND invoice_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """)[0][0] or 0
        stats["total_recurring_invoices"] = frappe.db.count("Recurring Invoice")
        stats["total_installments"] = frappe.db.count("Installment Agreement")
        stats["total_commissions"] = frappe.db.count("Sales Commission")

    if get_module_status("Clients"):
        stats["total_clients"] = frappe.db.count("Client")
        stats["credit_charged"] = frappe.db.sql("SELECT COALESCE(SUM(amount),0) FROM `tabCredit Charge`")[0][0] or 0
        stats["credit_used"] = frappe.db.sql("SELECT COALESCE(SUM(amount),0) FROM `tabCredit Usage`")[0][0] or 0

    if get_module_status("Inventory"):
        stats["total_products"] = frappe.db.count("Product")
        stats["total_stock_value"] = frappe.db.sql("""
            SELECT COALESCE(SUM(COALESCE(current_stock, 0) * COALESCE(selling_price, 0)), 0) FROM `tabProduct`
        """)[0][0] or 0

    if get_module_status("Purchases"):
        stats["total_suppliers"] = frappe.db.count("Supplier")
        stats["pending_orders"] = frappe.db.count("Purchase Order", {"status": "Submitted"})

    if get_module_status("HR"):
        stats["total_employees"] = frappe.db.count("Employee")
        stats["active_employees"] = frappe.db.count("Employee", {"status": "Active"})

    if get_module_status("Accounting"):
        stats["total_expenses"] = frappe.db.sql("SELECT COALESCE(SUM(amount),0) FROM `tabExpense`")[0][0] or 0
        stats["total_incomes"] = frappe.db.sql("SELECT COALESCE(SUM(amount),0) FROM `tabIncome`")[0][0] or 0
        stats["active_banks"] = frappe.db.count("Bank Registration", {"is_active": 1})
        stats["active_treasuries"] = frappe.db.count("Treasury", {"is_active": 1})

    if get_module_status("Bookings"):
        stats["total_bookings"] = frappe.db.count("Booking")

    if get_module_status("Time Tracking"):
        stats["total_time_entries"] = frappe.db.count("Time Entry")

    return stats


@frappe.whitelist()
def get_document_catalog():
    catalog = []
    for module, doctypes in DOCUMENT_CATALOG.items():
        for doctype in doctypes:
            catalog.append({
                "module": module,
                "doctype": doctype,
                "route": doctype.lower().replace(" ", "-"),
                "templates": PRINT_TEMPLATE_MATRIX.get(doctype, []),
                "has_print": bool(PRINT_TEMPLATE_MATRIX.get(doctype)),
            })
    return catalog


@frappe.whitelist()
def get_dashboard_blueprint():
    from daftra.api import settings_api

    return {
        "sections": [
            {
                "key": "overview",
                "label": _("Overview"),
                "source": "daftra.api.dashboard_api.get_dashboard_stats",
            },
            {
                "key": "activity",
                "label": _("Recent Activity"),
                "source": "daftra.api.accounting_api.get_recent_activity",
            },
            {
                "key": "reports",
                "label": _("Reports"),
                "groups": reporting_api.get_reports_catalog(),
            },
            {
                "key": "settings",
                "label": _("Settings"),
                "groups": settings_api.get_settings_catalog(),
            },
            {
                "key": "plugins",
                "label": _("Manage Apps"),
                "items": settings_api.get_plugin_catalog(),
            },
        ]
    }


@frappe.whitelist()
def get_dashboard_overview():
    from daftra.api import settings_api

    return {
        "stats": get_dashboard_stats(),
        "modules": get_enabled_modules(),
        "setup": get_setup_state(),
        "reports": reporting_api.get_reports_catalog(),
        "settings": settings_api.get_settings_catalog(),
        "plugins": settings_api.get_plugin_catalog(),
        "readiness": settings_api.get_operational_readiness(),
    }
