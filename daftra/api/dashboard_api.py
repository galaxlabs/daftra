
import frappe
from frappe import _

@frappe.whitelist()
def get_module_status(module_name):
    """Check if a module is enabled"""
    settings = frappe.get_single('Daftra Settings')
    field = 'enable_' + module_name.lower() + '_module'
    return getattr(settings, field, 1)

@frappe.whitelist()
def get_enabled_modules():
    """Get all enabled modules"""
    settings = frappe.get_single('Daftra Settings')
    modules = ['Sales', 'Clients', 'Inventory', 'Purchases', 
               'Accounting', 'HR', 'POS', 'Bookings', 'Time Tracking', 'Tax']
    result = {}
    for m in modules:
        field = 'enable_' + m.lower() + '_module'
        result[m] = getattr(settings, field, 1)
    return result

@frappe.whitelist()
def get_dashboard_stats():
    """Get dashboard statistics"""
    from frappe.desk.doctype.notification_log.notification_log import get_notification_logs
    
    stats = {}
    
    # Sales stats
    if get_module_status('Sales'):
        stats['total_invoices'] = frappe.db.count('Sales Invoice')
        stats['total_invoice_amount'] = frappe.db.get_value(
            'Sales Invoice', {'docstatus': 1}, 'sum(total)') or 0
        stats['unpaid_invoices'] = frappe.db.count(
            'Sales Invoice', {'status': ['in', ['Unpaid', 'Overdue']]})
        stats['last_7_days_sales'] = frappe.db.sql("""
            SELECT COALESCE(SUM(total), 0) 
            FROM `tabSales Invoice` 
            WHERE docstatus = 1 
            AND invoice_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """)[0][0] or 0
    
    # Client stats
    if get_module_status('Clients'):
        stats['total_clients'] = frappe.db.count('Client')
    
    # Product stats
    if get_module_status('Inventory'):
        stats['total_products'] = frappe.db.count('Product')
        stats['total_stock_value'] = frappe.db.get_value(
            'Product', {}, 'sum(current_stock * selling_price)') or 0
    
    # Purchase stats
    if get_module_status('Purchases'):
        stats['total_suppliers'] = frappe.db.count('Supplier')
        stats['pending_orders'] = frappe.db.count(
            'Purchase Order', {'status': 'Submitted'})
    
    # HR stats
    if get_module_status('HR'):
        stats['total_employees'] = frappe.db.count('Employee')
        stats['active_employees'] = frappe.db.count(
            'Employee', {'status': 'Active'})
    
    # Finance stats
    if get_module_status('Accounting'):
        stats['total_expenses'] = frappe.db.sql(
            'SELECT COALESCE(SUM(amount),0) FROM `tabExpense`')[0][0] or 0
        stats['total_incomes'] = frappe.db.sql(
            'SELECT COALESCE(SUM(amount),0) FROM `tabIncome`')[0][0] or 0
    
    return stats
