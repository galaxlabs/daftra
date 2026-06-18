
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
