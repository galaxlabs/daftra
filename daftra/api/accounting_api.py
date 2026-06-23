import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate


def _safe_date(value, fallback=None):
    return getdate(value or fallback or nowdate())


def _sum(query, params=None):
    return flt((frappe.db.sql(query, params or (), as_list=True)[0][0]) or 0)


def _leaf_accounts():
    return frappe.get_all(
        "Account",
        fields=["name", "account_name", "account_number", "account_type", "balance"],
        filters={"is_group": 0},
        order_by="account_type asc, account_name asc",
    )


@frappe.whitelist()
def get_profit_loss(from_date=None, to_date=None):
    from_date = _safe_date(from_date, "2000-01-01")
    to_date = _safe_date(to_date)

    invoice_revenue = _sum(
        """
        SELECT COALESCE(SUM(total), 0)
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND invoice_date BETWEEN %s AND %s
        """,
        (from_date, to_date),
    )
    direct_income = _sum(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabIncome`
        WHERE income_date BETWEEN %s AND %s
        """,
        (from_date, to_date),
    )
    purchase_cost = _sum(
        """
        SELECT COALESCE(SUM(total), 0)
        FROM `tabPurchase Invoice`
        WHERE docstatus = 1 AND invoice_date BETWEEN %s AND %s
        """,
        (from_date, to_date),
    )
    direct_expenses = _sum(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabExpense`
        WHERE expense_date BETWEEN %s AND %s
        """,
        (from_date, to_date),
    )

    total_income = invoice_revenue + direct_income
    total_expenses = purchase_cost + direct_expenses
    gross_profit = invoice_revenue - purchase_cost
    net_profit = total_income - total_expenses

    return {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "income": {
            "sales_invoices": invoice_revenue,
            "direct_income": direct_income,
            "total": total_income,
        },
        "expenses": {
            "purchase_invoices": purchase_cost,
            "direct_expenses": direct_expenses,
            "total": total_expenses,
        },
        "gross_profit": gross_profit,
        "net_profit": net_profit,
        "profit": net_profit,
    }


@frappe.whitelist()
def get_balance_sheet(as_of_date=None):
    as_of_date = _safe_date(as_of_date)
    totals = {"assets": 0, "liabilities": 0, "equity": 0}
    details = {"assets": [], "liabilities": [], "equity": []}

    type_map = {"asset": "assets", "liability": "liabilities", "equity": "equity"}
    for acc in _leaf_accounts():
        bucket = type_map.get((acc.account_type or "").lower())
        if not bucket:
            continue
        balance = flt(acc.balance)
        totals[bucket] += balance
        details[bucket].append({
            "account": acc.name,
            "account_name": acc.account_name,
            "account_number": acc.account_number,
            "balance": balance,
        })

    receivables = _sum(
        """
        SELECT COALESCE(SUM(balance), 0)
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND invoice_date <= %s
        """,
        (as_of_date,),
    )
    payables = _sum(
        """
        SELECT COALESCE(SUM(total - COALESCE(paid_amount, 0)), 0)
        FROM `tabPurchase Invoice`
        WHERE docstatus = 1 AND invoice_date <= %s
        """,
        (as_of_date,),
    )

    return {
        "as_of_date": str(as_of_date),
        "totals": totals,
        "details": details,
        "working_capital": totals["assets"] - totals["liabilities"],
        "receivables": receivables,
        "payables": payables,
    }


@frappe.whitelist()
def get_trial_balance(as_of_date=None):
    as_of_date = _safe_date(as_of_date)
    rows = []
    total_debit = 0
    total_credit = 0

    for acc in _leaf_accounts():
        balance = flt(acc.balance)
        debit = balance if balance > 0 else 0
        credit = abs(balance) if balance < 0 else 0
        total_debit += debit
        total_credit += credit
        rows.append({
            "account": acc.name,
            "account_name": acc.account_name,
            "account_type": acc.account_type,
            "debit": debit,
            "credit": credit,
            "balance": balance,
        })

    return {
        "as_of_date": str(as_of_date),
        "rows": rows,
        "total_debit": total_debit,
        "total_credit": total_credit,
    }


@frappe.whitelist()
def get_recent_activity(limit=20):
    limit = int(limit or 20)
    events = []
    doctypes = [
        ("Sales Invoice", ["name", "modified", "modified_by", "status", "total"], "modified desc"),
        ("Purchase Invoice", ["name", "modified", "modified_by", "status", "total"], "modified desc"),
        ("Journal Entry", ["name", "modified", "modified_by", "entry_type", "total_debit", "total_credit"], "modified desc"),
        ("Invoice Payment", ["name", "modified", "modified_by", "payment_method", "amount"], "modified desc"),
        ("Supplier Payment", ["name", "modified", "modified_by", "payment_method", "amount"], "modified desc"),
        ("Expense", ["name", "modified", "modified_by", "amount", "vendor"], "modified desc"),
        ("Income", ["name", "modified", "modified_by", "amount", "reference"], "modified desc"),
        ("POS Session", ["name", "modified", "modified_by", "status", "total_sales"], "modified desc"),
    ]
    for doctype, fields, order_by in doctypes:
        if not frappe.db.exists("DocType", doctype):
            continue
        docs = frappe.get_all(doctype, fields=fields, order_by=order_by, limit_page_length=min(limit, 10))
        for doc in docs:
            payload = dict(doc)
            payload["doctype"] = doctype
            events.append(payload)

    events.sort(key=lambda row: str(row.get("modified") or ""), reverse=True)
    return events[:limit]


@frappe.whitelist()
def get_bank_registrations(active_only=1):
    filters = {}
    if int(active_only or 0):
        filters["is_active"] = 1
    return frappe.get_all(
        "Bank Registration",
        filters=filters,
        fields=[
            "name",
            "bank_name",
            "account_title",
            "account_number",
            "iban",
            "currency",
            "current_balance",
            "linked_treasury",
            "is_default",
        ],
        order_by="is_default desc, modified desc",
    )
