
import frappe
from frappe import _

@frappe.whitelist()
def get_profit_loss(from_date, to_date):
    """Get profit & loss statement"""
    income = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabIncome`
        WHERE income_date BETWEEN %s AND %s
    """, (from_date, to_date))[0][0]
    
    expenses = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabExpense`
        WHERE expense_date BETWEEN %s AND %s
    """, (from_date, to_date))[0][0]
    
    return {
        'income': income,
        'expenses': expenses,
        'profit': income - expenses
    }

@frappe.whitelist()
def get_balance_sheet():
    """Get balance sheet"""
    accounts = frappe.get_all('Account', 
        fields=['name', 'account_type', 'balance'],
        filters={'is_group': 0})
    
    result = {'assets': 0, 'liabilities': 0, 'equity': 0}
    for acc in accounts:
        atype = acc.account_type.lower()
        if atype in result:
            result[atype] += acc.balance or 0
    
    return result



@frappe.whitelist()
def get_bank_registrations(active_only=1):
    filters = {}
    if int(active_only or 0):
        filters['is_active'] = 1
    return frappe.get_all(
        'Bank Registration',
        filters=filters,
        fields=[
            'name',
            'bank_name',
            'account_title',
            'account_number',
            'iban',
            'currency',
            'current_balance',
            'linked_treasury',
            'is_default',
        ],
        order_by='is_default desc, modified desc',
    )
