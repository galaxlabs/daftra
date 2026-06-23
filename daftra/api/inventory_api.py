import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_product_price(product_name, price_list=None, qty=1):
    qty = flt(qty or 1)
    filters = {"product": product_name}
    if price_list:
        filters["price_list"] = price_list
    rules = frappe.get_all(
        "Price List Rule",
        filters=filters,
        fields=["name", "rate", "min_qty", "max_qty", "price_list"],
        order_by="min_qty desc, modified desc",
    )
    for rule in rules:
        min_qty = flt(rule.min_qty)
        max_qty = flt(rule.max_qty)
        if qty >= min_qty and (not max_qty or qty <= max_qty):
            return {"price": flt(rule.rate), "source": "Price List Rule", "rule": rule.name, "price_list": rule.price_list}

    return {
        "price": flt(frappe.db.get_value("Product", product_name, "selling_price") or 0),
        "source": "Product",
        "price_list": price_list,
    }
