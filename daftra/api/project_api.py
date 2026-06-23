import json

import frappe
from frappe import _
from frappe.utils import flt

ROOT_COST_CENTER_NAME = "Projects"


def _payload_dict(payload):
    if isinstance(payload, str):
        payload = json.loads(payload or "{}")
    return payload or {}


def _series_for(doctype):
    meta = frappe.get_meta(doctype)
    field = meta.get_field("naming_series")
    if field and field.options:
        return field.options.split("\n")[0]
    return None


def _prepare_series(doc):
    if doc.meta.has_field("naming_series") and not getattr(doc, "naming_series", None):
        doc.naming_series = _series_for(doc.doctype)


def _save(doc):
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    return doc


def _get_or_create_root_cost_center():
    root = frappe.db.get_value("Cost Center", {"cost_center_name": ROOT_COST_CENTER_NAME}, "name")
    if root:
        return frappe.get_doc("Cost Center", root)
    doc = frappe.new_doc("Cost Center")
    doc.cost_center_name = ROOT_COST_CENTER_NAME
    doc.is_group = 1
    doc.budget_amount = 0
    _prepare_series(doc)
    return _save(doc)


def ensure_project_cost_center(project_name):
    project = frappe.get_doc("Daftra Project", project_name)
    if project.project_cost_center:
        return project.project_cost_center

    root = _get_or_create_root_cost_center()
    center = frappe.new_doc("Cost Center")
    center.cost_center_name = f"{project.project_code} - {project.project_name}"
    center.parent_cost_center = root.name
    center.is_group = 0
    center.budget_amount = flt(project.budget_amount)
    _prepare_series(center)
    center = _save(center)

    project.db_set("project_cost_center", center.name, update_modified=False)
    return center.name




def sync_project_cost_center(doc, project_field='project', cost_center_field='cost_center'):
    project_name = getattr(doc, project_field, None)
    if project_name and not getattr(doc, cost_center_field, None):
        setattr(doc, cost_center_field, ensure_project_cost_center(project_name))
    return getattr(doc, cost_center_field, None)

def _sum_sql(query, params):
    return frappe.db.sql(query, params)[0][0] or 0


def refresh_project_document(doc, method=None):
    try:
        return refresh_project_financials(doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Project financial refresh failed")
        return None


def refresh_project_from_doc(doc, method=None):
    project_name = getattr(doc, "project", None)
    if not project_name:
        return None
    try:
        return refresh_project_financials(project_name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Project financial refresh failed")
        return None


def refresh_project_financials(project_name):
    project = frappe.get_doc("Daftra Project", project_name)
    cost_center = project.project_cost_center or ensure_project_cost_center(project_name)

    revenue = 0
    revenue += _sum_sql(
        """
        SELECT COALESCE(SUM(total), 0)
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND (project = %s OR cost_center = %s)
        """,
        (project_name, cost_center),
    )
    revenue += _sum_sql(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabIncome`
        WHERE (project = %s OR cost_center = %s)
        """,
        (project_name, cost_center),
    )

    cost = 0
    cost += _sum_sql(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabExpense`
        WHERE (project = %s OR cost_center = %s)
        """,
        (project_name, cost_center),
    )
    cost += _sum_sql(
        """
        SELECT COALESCE(SUM(total), 0)
        FROM `tabPurchase Invoice`
        WHERE docstatus < 2 AND (project = %s OR cost_center = %s)
        """,
        (project_name, cost_center),
    )
    cost += _sum_sql(
        """
        SELECT COALESCE(SUM(COALESCE(cost_amount, 0)), 0)
        FROM `tabTime Entry`
        WHERE (project = %s OR cost_center = %s)
        """,
        (project_name, cost_center),
    )
    cost += _sum_sql(
        """
        SELECT COALESCE(SUM(COALESCE(debit, 0)), 0)
        FROM `tabJournal Entry Account` jea
        JOIN `tabJournal Entry` je ON je.name = jea.parent
        WHERE je.docstatus < 2 AND (je.project = %s OR je.cost_center = %s OR jea.cost_center = %s)
        """,
        (project_name, cost_center, cost_center),
    )

    profit = revenue - cost
    margin = (profit / revenue * 100) if revenue else 0

    project.db_set("actual_revenue", revenue, update_modified=False)
    project.db_set("actual_cost", cost, update_modified=False)
    project.db_set("profit", profit, update_modified=False)
    project.db_set("margin_percent", margin, update_modified=False)
    return {"project": project.name, "cost_center": cost_center, "revenue": revenue, "cost": cost, "profit": profit, "margin_percent": margin}


@frappe.whitelist()
def create_project_record(payload=None):
    payload = _payload_dict(payload)
    project = frappe.new_doc("Daftra Project")
    project.project_code = payload.get("project_code") or f"PRJ-{frappe.generate_hash(length=6).upper()}"
    project.project_name = payload.get("project_name") or "Project"
    client_value = payload.get("client") or payload.get("client_name")
    if client_value and frappe.db.exists("Client", client_value):
        project.client = client_value
    else:
        project.client = None
    project.project_type = payload.get("project_type") or "Service Project"
    project.status = payload.get("status") or "Draft"
    project.start_date = payload.get("start_date") or None
    project.end_date = payload.get("end_date") or None
    project.budget_amount = payload.get("budget_amount") or 0
    project.expected_revenue = payload.get("expected_revenue") or 0
    project.description = payload.get("description") or ""
    project.notes = payload.get("notes") or ""
    _prepare_series(project)
    project = _save(project)
    cost_center = ensure_project_cost_center(project.name)
    summary = refresh_project_financials(project.name)
    data = project.as_dict()
    data['cost_center'] = cost_center
    data['cost_center_name'] = frappe.db.get_value('Cost Center', cost_center, 'cost_center_name')
    data['summary'] = summary
    return data


@frappe.whitelist()
def get_project_profitability(project_name):
    project = frappe.get_doc("Daftra Project", project_name)
    if not project.project_cost_center:
        ensure_project_cost_center(project.name)
        project.reload()
    summary = refresh_project_financials(project.name)
    return {
        "project": project.name,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "cost_center": project.project_cost_center,
        "budget_amount": project.budget_amount,
        "revenue": project.actual_revenue,
        "cost": project.actual_cost,
        "profit": project.profit,
        "margin_percent": project.margin_percent,
        "summary": summary,
    }
