import frappe
from frappe import _
from frappe.utils import nowdate


def _copy_item_row(row):
    return {
        "product": row.product,
        "description": row.description,
        "qty": row.qty,
        "rate": row.rate,
        "amount": row.amount,
        "vat_rate": getattr(row, "vat_rate", 0),
        "vat_amount": getattr(row, "vat_amount", 0),
    }


@frappe.whitelist()
def create_purchase_quotation_from_request(request_name, supplier=None, valid_till=None):
    request = frappe.get_doc("Purchase Request", request_name)
    quotation = frappe.new_doc("Purchase Quotation")
    quotation.supplier = supplier or None
    quotation.quotation_date = nowdate()
    quotation.valid_till = valid_till or None
    quotation.status = "Sent" if supplier else "Draft"
    quotation.insert(ignore_permissions=True)
    if request.docstatus == 1:
        request.db_set("status", "Approved", update_modified=False)
    return quotation.name


@frappe.whitelist()
def create_purchase_order_from_quotation(quotation_name):
    quotation = frappe.get_doc("Purchase Quotation", quotation_name)
    if not quotation.supplier:
        frappe.throw(_("Supplier is required before creating a purchase order"))

    order = frappe.new_doc("Purchase Order")
    order.supplier = quotation.supplier
    order.order_date = nowdate()
    order.expected_delivery = quotation.valid_till or None
    order.currency = getattr(quotation, "currency", None) or "SAR"
    order.notes = _("Created from purchase quotation {0}").format(quotation.name)
    for row in quotation.get("items") or []:
        order.append("items", _copy_item_row(row))
    order.insert(ignore_permissions=True)

    quotation.db_set("status", "Accepted", update_modified=False)
    return order.name


@frappe.whitelist()
def create_purchase_invoice_from_order(order_name, submit_invoice=0):
    order = frappe.get_doc("Purchase Order", order_name)

    invoice = frappe.new_doc("Purchase Invoice")
    invoice.supplier = order.supplier
    invoice.invoice_date = nowdate()
    invoice.currency = order.currency or "SAR"
    invoice.notes = _("Created from purchase order {0}").format(order.name)
    if getattr(order, "project", None):
        invoice.project = order.project
    if getattr(order, "cost_center", None):
        invoice.cost_center = order.cost_center
    for row in order.get("items") or []:
        invoice.append("items", _copy_item_row(row))
    invoice.insert(ignore_permissions=True)

    if int(submit_invoice):
        invoice.submit()
        order.db_set("status", "Received", update_modified=False)
    elif order.docstatus == 1:
        order.db_set("status", "Partially Received", update_modified=False)

    return invoice.name
