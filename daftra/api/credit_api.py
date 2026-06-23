import frappe
from frappe import _
from frappe.utils import flt


def _sum_amount(doctype, client, credit_type=None, exclude_name=None):
    filters = {"client": client}
    if credit_type:
        filters["credit_type"] = credit_type
    if exclude_name:
        filters["name"] = ["!=", exclude_name]
    return flt(frappe.db.get_value(doctype, filters, "sum(amount)") or 0)


def get_client_credit_balance(client, credit_type=None, exclude_usage=None):
    charged = _sum_amount("Credit Charge", client, credit_type)
    used = _sum_amount("Credit Usage", client, credit_type, exclude_name=exclude_usage)
    return flt(charged - used)


def apply_credit_defaults(doc):
    package = None
    if getattr(doc, "credit_package", None):
        package = frappe.get_doc("Credit Package", doc.credit_package)
        if not package.active:
            frappe.throw(_("Credit package must be active"))
        if package.credit_type:
            if doc.credit_type and doc.credit_type != package.credit_type:
                frappe.throw(_("Credit package does not belong to the selected credit type"))
            doc.credit_type = package.credit_type
        if not flt(doc.amount):
            doc.amount = package.credits
    if getattr(doc, "credit_type", None):
        credit_type = frappe.get_doc("Credit Type", doc.credit_type)
        if not credit_type.active:
            frappe.throw(_("Credit type must be active"))
        if not flt(doc.amount) and flt(credit_type.default_credits):
            doc.amount = credit_type.default_credits
    if not doc.client:
        frappe.throw(_("Client is required"))
    if flt(doc.amount) <= 0:
        frappe.throw(_("Credit amount must be greater than zero"))
    doc.amount = flt(doc.amount)
    if package and not getattr(doc, "notes", None):
        doc.notes = _("Applied from credit package {0}").format(package.package_name)


@frappe.whitelist()
def get_client_credit_summary(client_name):
    if not client_name:
        frappe.throw(_("Client is required"))

    charges = frappe.get_all(
        "Credit Charge",
        filters={"client": client_name},
        fields=["name", "credit_type", "credit_package", "amount", "creation"],
        order_by="creation desc",
        limit_page_length=10,
    )
    usages = frappe.get_all(
        "Credit Usage",
        filters={"client": client_name},
        fields=["name", "credit_type", "credit_package", "reference_invoice", "amount", "creation"],
        order_by="creation desc",
        limit_page_length=10,
    )
    charged = _sum_amount("Credit Charge", client_name)
    used = _sum_amount("Credit Usage", client_name)

    by_type = []
    for credit_type in frappe.get_all("Credit Type", filters={"active": 1}, fields=["name", "type_name", "unit_label"]):
        balance = get_client_credit_balance(client_name, credit_type.name)
        if balance or frappe.db.exists("Credit Charge", {"client": client_name, "credit_type": credit_type.name}) or frappe.db.exists("Credit Usage", {"client": client_name, "credit_type": credit_type.name}):
            by_type.append(
                {
                    "credit_type": credit_type.name,
                    "label": credit_type.type_name,
                    "unit_label": credit_type.unit_label or "Credits",
                    "balance": balance,
                }
            )

    return {
        "client": client_name,
        "charged": charged,
        "used": used,
        "balance": flt(charged - used),
        "recent_charges": charges,
        "recent_usages": usages,
        "by_type": by_type,
    }
