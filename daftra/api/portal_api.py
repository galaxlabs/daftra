import frappe
from frappe import _


def _party_doc(party_type, party_name):
    if party_type not in {"Client", "Supplier"}:
        frappe.throw(_("Unsupported party type"))
    return frappe.get_doc(party_type, party_name)


@frappe.whitelist()
def create_party_portal_user(party_type, party_name, email=None):
    party = _party_doc(party_type, party_name)
    email = email or getattr(party, "email", None)
    if not email:
        frappe.throw(_("Email is required to create a portal user"))

    user_name = frappe.db.get_value("User", email, "name")
    if user_name:
        user = frappe.get_doc("User", user_name)
    else:
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = getattr(party, "business_name", None) or getattr(party, "supplier_name", None) or getattr(party, "first_name", None) or party_name
        user.enabled = 1
        user.user_type = "Website User"
        user.send_welcome_email = 0
        user.insert(ignore_permissions=True)

    existing_roles = {row.role for row in user.get("roles") or []}
    for role in ["Website User", "Customer", "Supplier"]:
        if frappe.db.exists("Role", role) and role not in existing_roles:
            if party_type == "Client" and role == "Supplier":
                continue
            if party_type == "Supplier" and role == "Customer":
                continue
            user.append("roles", {"role": role})
    user.save(ignore_permissions=True)

    return {
        "user": user.name,
        "email": user.email,
        "party_type": party_type,
        "party_name": party_name,
    }


@frappe.whitelist()
def get_party_portal_documents(party_type, party_name):
    _party_doc(party_type, party_name)
    if party_type == "Client":
        return {
            "quotations": frappe.get_all("Sales Quotation", filters={"client": party_name}, fields=["name", "quotation_date", "valid_till", "status", "total"], order_by="modified desc", limit_page_length=20),
            "invoices": frappe.get_all("Sales Invoice", filters={"client": party_name}, fields=["name", "invoice_date", "due_date", "status", "total", "balance"], order_by="modified desc", limit_page_length=20),
            "payments": frappe.get_all("Invoice Payment", fields=["name", "sales_invoice", "payment_date", "amount", "payment_method"], filters=[["Invoice Payment", "sales_invoice", "in", frappe.get_all("Sales Invoice", filters={"client": party_name}, pluck="name") or [""]]], order_by="modified desc", limit_page_length=20),
            "appointments": frappe.get_all("Appointment", filters={"client": party_name}, fields=["name", "appointment_date", "appointment_time", "status"], order_by="modified desc", limit_page_length=20),
            "bookings": frappe.get_all("Booking", filters={"client": party_name}, fields=["name", "booking_date", "booking_time", "service", "status"], order_by="modified desc", limit_page_length=20),
        }

    return {
        "quotations": frappe.get_all("Purchase Quotation", filters={"supplier": party_name}, fields=["name", "quotation_date", "valid_till", "status", "total"], order_by="modified desc", limit_page_length=20),
        "orders": frappe.get_all("Purchase Order", filters={"supplier": party_name}, fields=["name", "order_date", "expected_delivery", "status", "total"], order_by="modified desc", limit_page_length=20),
        "invoices": frappe.get_all("Purchase Invoice", filters={"supplier": party_name}, fields=["name", "invoice_date", "due_date", "status", "total", "paid_amount"], order_by="modified desc", limit_page_length=20),
        "payments": frappe.get_all("Supplier Payment", fields=["name", "purchase_invoice", "payment_date", "amount", "payment_method"], filters=[["Supplier Payment", "purchase_invoice", "in", frappe.get_all("Purchase Invoice", filters={"supplier": party_name}, pluck="name") or [""]]], order_by="modified desc", limit_page_length=20),
    }
