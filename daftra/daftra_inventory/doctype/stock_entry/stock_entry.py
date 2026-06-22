import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class StockEntry(Document):
    def validate(self):
        if not self.date:
            self.date = nowdate()
        for row in self.get("items") or []:
            row.qty = flt(row.qty)
            row.rate = flt(row.rate)
            if row.qty <= 0:
                frappe.throw("Stock quantity must be greater than zero")
            row.amount = row.qty * row.rate

    def on_submit(self):
        sign = -1 if self.entry_type == "Material Issue" else 1
        for row in self.get("items") or []:
            if row.product and frappe.db.exists("Product", row.product):
                product = frappe.get_doc("Product", row.product)
                product.current_stock = flt(product.current_stock) + (sign * flt(row.qty))
                if flt(product.current_stock) < 0:
                    frappe.throw(f"Product {product.product_name} cannot have negative stock")
                product.save(ignore_permissions=True)
