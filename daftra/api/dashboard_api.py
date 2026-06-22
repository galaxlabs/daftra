import frappe
from frappe import _

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

@frappe.whitelist()
def get_module_status(module_name):
    """Check if a Daftra module is enabled."""
    settings = frappe.get_single("Daftra Settings")
    field = MODULE_FIELDS.get(module_name)
    if not field:
        field = "enable_" + frappe.scrub(module_name).replace("daftra_", "") + "_module"
    return getattr(settings, field, 1)

@frappe.whitelist()
def get_enabled_modules():
    """Get all enabled Daftra modules."""
    settings = frappe.get_single("Daftra Settings")
    return {module: getattr(settings, field, 1) for module, field in MODULE_FIELDS.items()}

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

    if get_module_status("Clients"):
        stats["total_clients"] = frappe.db.count("Client")

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

    return stats
