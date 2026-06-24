import frappe
from frappe import _
from frappe.utils import nowdate


def _copy_item_row(row):
    product_code = getattr(row, "product", None) or getattr(row, "item", None)
    return {
        "product": product_code,
        "description": getattr(row, "description", None),
        "qty": getattr(row, "qty", 0),
        "rate": getattr(row, "rate", 0),
        "amount": getattr(row, "amount", 0),
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



def _get_item_source_rows(doc):
    return doc.get("items") or []


@frappe.whitelist()
def copy_procurement_document_draft(source_doctype, source_name, target_doctype, supplier=None):
    source = frappe.get_doc(source_doctype, source_name)

    if target_doctype == "Purchase Quotation":
        target = frappe.new_doc("Purchase Quotation")
        target.supplier = supplier or getattr(source, "supplier", None)
        target.quotation_date = nowdate()
        target.currency = getattr(source, "currency", None) or "SAR"
        target.status = "Draft"
        if source_doctype == "Purchase Request":
            target.source_purchase_request = source.name
        elif source_doctype == "Sales Quotation":
            target.sales_quotation_reference = source.name
        elif source_doctype == "Sales Invoice":
            target.proforma_invoice_reference = source.name
        for row in _get_item_source_rows(source):
            target.append("items", _copy_item_row(row))
        target.insert(ignore_permissions=True)
        return target.name

    if target_doctype == "Purchase Order":
        if source_doctype == "Purchase Quotation":
            return create_purchase_order_from_quotation(source.name)
        target = frappe.new_doc("Purchase Order")
        target.supplier = supplier or getattr(source, "supplier", None)
        target.order_date = nowdate()
        target.currency = getattr(source, "currency", None) or "SAR"
        target.status = "Draft"
        if source_doctype == "Sales Quotation":
            target.sales_quotation_reference = source.name
        elif source_doctype == "Sales Invoice":
            target.proforma_invoice_reference = source.name
        for row in _get_item_source_rows(source):
            target.append("items", _copy_item_row(row))
        target.insert(ignore_permissions=True)
        return target.name

    if target_doctype == "Purchase Invoice":
        if source_doctype == "Purchase Order":
            return create_purchase_invoice_from_order(source.name, submit_invoice=0)
        target = frappe.new_doc("Purchase Invoice")
        target.supplier = supplier or getattr(source, "supplier", None)
        target.invoice_date = nowdate()
        target.currency = getattr(source, "currency", None) or "SAR"
        target.status = "Draft"
        if source_doctype == "Purchase Quotation":
            target.source_purchase_quotation = source.name
            target.supplier_quotation_no = getattr(source, "supplier_quotation_no", None)
            target.sales_quotation_reference = getattr(source, "sales_quotation_reference", None)
            target.customer_purchase_order_no = getattr(source, "customer_purchase_order_no", None)
            target.proforma_invoice_reference = getattr(source, "proforma_invoice_reference", None)
        elif source_doctype == "Sales Invoice":
            target.proforma_invoice_reference = source.name
        for row in _get_item_source_rows(source):
            target.append("items", _copy_item_row(row))
        target.insert(ignore_permissions=True)
        return target.name

    frappe.throw(_("Unsupported target doctype for copy"))
