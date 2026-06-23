import frappe
from frappe.utils import flt, getdate, nowdate


REPORT_GROUPS = {
    "invoices": {"label": "Sales Reports", "reports": ["sales_summary", "receivables", "invoice_status"]},
    "purchase_orders": {"label": "Purchase Reports", "reports": ["purchase_summary", "supplier_balances", "purchase_status"]},
    "accounting": {"label": "Accounting Reports", "reports": ["profit_loss", "balance_sheet", "trial_balance", "cash_position"]},
    "sms_reports": {"label": "POS Reports", "reports": ["pos_summary"]},
    "credits_reports": {"label": "Credits Reports", "reports": ["credits_summary"]},
    "workflows": {"label": "Workflow Reports", "reports": ["workflow_summary"]},
    "clients": {"label": "Client Reports", "reports": ["client_summary", "client_outstanding"]},
    "inventory": {"label": "Inventory Reports", "reports": ["inventory_summary", "stock_alerts", "price_rules"]},
    "time_tracking": {"label": "Time Tracking Reports", "reports": ["time_tracking_summary"]},
}


def _safe_date(value, fallback=None):
    return getdate(value or fallback or nowdate())


def _sum(query, params=None):
    return flt((frappe.db.sql(query, params or (), as_list=True)[0][0]) or 0)


@frappe.whitelist()
def get_reports_catalog():
    return REPORT_GROUPS


@frappe.whitelist()
def get_sales_report(from_date=None, to_date=None):
    from_date = _safe_date(from_date, "2000-01-01")
    to_date = _safe_date(to_date)
    total_invoices = frappe.db.count("Sales Invoice", {"docstatus": 1, "invoice_date": ["between", [from_date, to_date]]})
    total_sales = _sum("SELECT COALESCE(SUM(total),0) FROM `tabSales Invoice` WHERE docstatus = 1 AND invoice_date BETWEEN %s AND %s", (from_date, to_date))
    paid_sales = _sum("SELECT COALESCE(SUM(paid_amount),0) FROM `tabSales Invoice` WHERE docstatus = 1 AND invoice_date BETWEEN %s AND %s", (from_date, to_date))
    outstanding = _sum("SELECT COALESCE(SUM(balance),0) FROM `tabSales Invoice` WHERE docstatus = 1 AND invoice_date BETWEEN %s AND %s", (from_date, to_date))
    status_breakdown = frappe.get_all("Sales Invoice", filters={"docstatus": 1, "invoice_date": ["between", [from_date, to_date]]}, fields=["status", "count(name) as count"], group_by="status")
    return {"from_date": str(from_date), "to_date": str(to_date), "total_invoices": total_invoices, "total_sales": total_sales, "paid_sales": paid_sales, "outstanding": outstanding, "status_breakdown": status_breakdown}


@frappe.whitelist()
def get_purchase_report(from_date=None, to_date=None):
    from_date = _safe_date(from_date, "2000-01-01")
    to_date = _safe_date(to_date)
    total_invoices = frappe.db.count("Purchase Invoice", {"docstatus": 1, "invoice_date": ["between", [from_date, to_date]]})
    total_purchases = _sum("SELECT COALESCE(SUM(total),0) FROM `tabPurchase Invoice` WHERE docstatus = 1 AND invoice_date BETWEEN %s AND %s", (from_date, to_date))
    paid = _sum("SELECT COALESCE(SUM(paid_amount),0) FROM `tabPurchase Invoice` WHERE docstatus = 1 AND invoice_date BETWEEN %s AND %s", (from_date, to_date))
    payable = _sum("SELECT COALESCE(SUM(total - COALESCE(paid_amount,0)),0) FROM `tabPurchase Invoice` WHERE docstatus = 1 AND invoice_date BETWEEN %s AND %s", (from_date, to_date))
    supplier_count = frappe.db.count("Supplier")
    return {"from_date": str(from_date), "to_date": str(to_date), "total_invoices": total_invoices, "total_purchases": total_purchases, "paid": paid, "payable": payable, "supplier_count": supplier_count}


@frappe.whitelist()
def get_inventory_report():
    low_stock = [
        row for row in frappe.get_all("Product", filters={"status": "Active"}, fields=["name", "product_code", "product_name", "current_stock", "minimum_stock"], limit_page_length=200)
        if flt(row.get("current_stock")) < flt(row.get("minimum_stock"))
    ][:20]
    total_products = frappe.db.count("Product")
    stock_value = _sum("SELECT COALESCE(SUM(COALESCE(current_stock,0) * COALESCE(selling_price,0)),0) FROM `tabProduct`")
    total_warehouses = frappe.db.count("Warehouse", {"status": "Active"})
    price_rules = frappe.db.count("Price List Rule")
    return {"total_products": total_products, "stock_value": stock_value, "total_warehouses": total_warehouses, "price_rules": price_rules, "low_stock": low_stock}


@frappe.whitelist()
def get_clients_report():
    total_clients = frappe.db.count("Client")
    business_clients = frappe.db.count("Client", {"client_type": "Business"})
    individual_clients = frappe.db.count("Client", {"client_type": "Individual"})
    outstanding = _sum("SELECT COALESCE(SUM(balance),0) FROM `tabSales Invoice` WHERE docstatus = 1")
    top_clients = frappe.db.sql("""
        SELECT client, COALESCE(SUM(total),0) as sales
        FROM `tabSales Invoice`
        WHERE docstatus = 1
        GROUP BY client
        ORDER BY sales DESC
        LIMIT 10
    """, as_dict=True)
    return {"total_clients": total_clients, "business_clients": business_clients, "individual_clients": individual_clients, "outstanding": outstanding, "top_clients": top_clients}


@frappe.whitelist()
def get_credits_report():
    charged = _sum("SELECT COALESCE(SUM(amount),0) FROM `tabCredit Charge`")
    used = _sum("SELECT COALESCE(SUM(amount),0) FROM `tabCredit Usage`")
    active_packages = frappe.db.count("Credit Package", {"active": 1})
    active_types = frappe.db.count("Credit Type", {"active": 1})
    return {"charged": charged, "used": used, "balance": charged - used, "active_packages": active_packages, "active_types": active_types}


@frappe.whitelist()
def get_workflow_report():
    return {
        "sales_quotations": frappe.db.count("Sales Quotation"),
        "purchase_requests": frappe.db.count("Purchase Request"),
        "purchase_orders": frappe.db.count("Purchase Order"),
        "bookings": frappe.db.count("Booking"),
        "maintenance_orders": frappe.db.count("Maintenance Order"),
        "recurring_invoices": frappe.db.count("Recurring Invoice"),
        "installment_agreements": frappe.db.count("Installment Agreement"),
    }


@frappe.whitelist()
def get_time_tracking_report(from_date=None, to_date=None):
    from_date = _safe_date(from_date, "2000-01-01")
    to_date = _safe_date(to_date)
    total_entries = frappe.db.count("Time Entry", {"date": ["between", [from_date, to_date]]})
    total_hours = _sum("SELECT COALESCE(SUM(duration_hours),0) FROM `tabTime Entry` WHERE date BETWEEN %s AND %s", (from_date, to_date))
    total_billable = _sum("SELECT COALESCE(SUM(COALESCE(billable_amount,0)),0) FROM `tabTime Entry` WHERE date BETWEEN %s AND %s", (from_date, to_date))
    total_cost = _sum("SELECT COALESCE(SUM(COALESCE(cost_amount,0)),0) FROM `tabTime Entry` WHERE date BETWEEN %s AND %s", (from_date, to_date))
    return {"from_date": str(from_date), "to_date": str(to_date), "total_entries": total_entries, "total_hours": total_hours, "total_billable": total_billable, "total_cost": total_cost}


@frappe.whitelist()
def get_pos_report(from_date=None, to_date=None):
    from_date = _safe_date(from_date, "2000-01-01")
    to_date = _safe_date(to_date)
    sessions = frappe.db.count("POS Session", {"opening_time": ["between", [f"{from_date} 00:00:00", f"{to_date} 23:59:59"]]})
    total_sales = _sum("SELECT COALESCE(SUM(total_sales),0) FROM `tabPOS Session` WHERE opening_time BETWEEN %s AND %s", (f"{from_date} 00:00:00", f"{to_date} 23:59:59"))
    opening_balance = _sum("SELECT COALESCE(SUM(opening_balance),0) FROM `tabPOS Session` WHERE opening_time BETWEEN %s AND %s", (f"{from_date} 00:00:00", f"{to_date} 23:59:59"))
    closing_balance = _sum("SELECT COALESCE(SUM(closing_balance),0) FROM `tabPOS Session` WHERE opening_time BETWEEN %s AND %s", (f"{from_date} 00:00:00", f"{to_date} 23:59:59"))
    return {"from_date": str(from_date), "to_date": str(to_date), "sessions": sessions, "total_sales": total_sales, "opening_balance": opening_balance, "closing_balance": closing_balance}
