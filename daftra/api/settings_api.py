import frappe
from frappe.utils import cint

from daftra.api.dashboard_api import DOCUMENT_CATALOG, MODULE_FIELDS, get_enabled_modules


SETTINGS_GROUPS = [
    {"key": "sales_settings", "label": "Sales Settings", "pages": ["sales_settings", "invoice_layouts", "templates"], "module": "Sales"},
    {"key": "clients_settings", "label": "Client Settings", "pages": ["client_settings", "insurance_agents", "credit_types", "credit_packages"], "module": "Clients"},
    {"key": "inventory_settings", "label": "Inventory Settings", "pages": ["inventory_settings", "warehouses", "price_lists", "price_list_rules"], "module": "Inventory"},
    {"key": "purchase_settings", "label": "Purchase Settings", "pages": ["purchase_settings", "purchase_requests", "purchase_orders"], "module": "Purchases"},
    {"key": "finance_settings", "label": "Finance Settings", "pages": ["finance_settings", "accounting_settings", "chart_of_accounts", "cost_centers"], "module": "Accounting"},
    {"key": "hr_settings", "label": "HR Settings", "pages": ["hr_settings", "request_types", "employee_roles", "payroll"], "module": "HR"},
    {"key": "pos_settings", "label": "POS Settings", "pages": ["pos_settings", "pos_reports", "pos_sessions"], "module": "POS"},
    {"key": "time_tracking_settings", "label": "Time Tracking Settings", "pages": ["time_tracking_settings", "time_tracking_invoice"], "module": "Time Tracking"},
    {"key": "tax_settings", "label": "Taxes & VAT", "pages": ["taxes", "vat_settings"], "module": "Tax"},
    {"key": "workflow_settings", "label": "Workflow Settings", "pages": ["workflow_orders", "workflow_settings"], "module": "Settings"},
    {"key": "system_settings", "label": "System Settings", "pages": ["system_settings", "users", "roles", "plugin_manager"], "module": "Settings"},
]


def _module_enabled(module_name):
    if module_name == "Settings":
        return 1
    return cint(get_enabled_modules().get(module_name, 1))


def _active_service_count():
    return frappe.db.count("Product", {"product_type": "Service", "status": "Active"})


def _non_empty(value):
    return bool(str(value or "").strip())


@frappe.whitelist()
def get_settings_catalog():
    catalog = []
    for group in SETTINGS_GROUPS:
        catalog.append({
            **group,
            "enabled": _module_enabled(group["module"]),
        })
    return catalog


@frappe.whitelist()
def get_plugin_catalog():
    enabled_modules = get_enabled_modules()
    catalog = []
    for module, field in MODULE_FIELDS.items():
        catalog.append({
            "key": module.lower().replace(" ", "_"),
            "label": module,
            "enabled": cint(enabled_modules.get(module, 1)),
            "setting_field": field,
            "doctypes": DOCUMENT_CATALOG.get(module, []),
        })
    catalog.append({
        "key": "settings",
        "label": "Global & Settings",
        "enabled": 1,
        "setting_field": None,
        "doctypes": DOCUMENT_CATALOG.get("Settings", []),
    })
    return catalog


@frappe.whitelist()
def get_operational_readiness():
    settings = frappe.get_single("Daftra Settings")
    active_products = frappe.db.count("Product", {"status": "Active"})
    active_services = _active_service_count()
    active_warehouses = frappe.db.count("Warehouse", {"status": "Active"})
    active_banks = frappe.db.count("Bank Registration", {"is_active": 1})
    active_treasuries = frappe.db.count("Treasury", {"is_active": 1})
    active_employees = frappe.db.count("Employee", {"status": "Active"})
    active_shifts = frappe.db.count("Shift")

    checks = {
        "booking_service_ready": {
            "ok": active_services > 0,
            "count": active_services,
            "message": "Bookings require at least one active service.",
        },
        "pos_ready": {
            "ok": active_products > 0 and active_warehouses > 0 and (active_banks > 0 or active_treasuries > 0),
            "products": active_products,
            "warehouses": active_warehouses,
            "cash_sources": active_banks + active_treasuries,
            "message": "POS needs active products, a warehouse, and a treasury or bank.",
        },
        "zatca_ready": {
            "ok": (not cint(settings.enable_zatca)) or (_non_empty(settings.company_name) and _non_empty(settings.vat_number) and _non_empty(settings.default_sales_tax)),
            "message": "ZATCA requires company name, VAT number, and default sales tax.",
        },
        "hr_ready": {
            "ok": (not cint(settings.enable_hr_module)) or (active_employees > 0 and active_shifts >= 0),
            "employees": active_employees,
            "shifts": active_shifts,
            "message": "HR should have employees and shifts configured.",
        },
        "time_tracking_ready": {
            "ok": (not cint(settings.enable_time_tracking_module)) or active_services > 0,
            "services": active_services,
            "message": "Time tracking works best when service items exist for billing.",
        },
    }
    return checks
