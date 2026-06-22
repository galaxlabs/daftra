(function () {
  function money(value) { return flt(value || 0); }

  function calculate_item(row) {
    const qty = money(row.qty);
    const rate = money(row.rate);
    row.amount = qty * rate;
    row.vat_amount = row.amount * money(row.vat_rate) / 100;
  }

  function calculate_document(frm) {
    let subtotal = 0;
    let tax = 0;
    (frm.doc.items || []).forEach((row) => {
      calculate_item(row);
      subtotal += money(row.amount);
      tax += money(row.vat_amount);
    });
    if (frm.doc.subtotal !== undefined) frm.set_value("subtotal", subtotal);
    if (frm.doc.tax_amount !== undefined) frm.set_value("tax_amount", tax);
    if (frm.doc.total !== undefined) frm.set_value("total", subtotal - money(frm.doc.discount_amount) + tax);
    if (frm.doc.balance !== undefined) frm.set_value("balance", money(frm.doc.total) - money(frm.doc.paid_amount));
    frm.refresh_field("items");
  }

  function add_print_button(frm) {
    if (!frm.is_new()) {
      frm.add_custom_button(__("Preview Print"), () => frappe.set_route("print", frm.doc.doctype, frm.doc.name), __("Daftra"));
    }
  }

  frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
      add_print_button(frm);
      if (!frm.is_new()) {
        frm.add_custom_button(__("Record Payment"), () => {
          frappe.new_doc("Invoice Payment", {
            sales_invoice: frm.doc.name,
            client: frm.doc.client,
            amount: frm.doc.balance || frm.doc.total || 0
          });
        }, __("Daftra"));
        frm.add_custom_button(__("ZATCA QR"), () => {
          frappe.call({
            method: "daftra.api.zatca_api.get_zatca_qr",
            args: { invoice_name: frm.doc.name },
            callback(r) {
              frappe.msgprint({
                title: __("ZATCA QR Data"),
                message: `<pre>${frappe.utils.escape_html(JSON.stringify(r.message || {}, null, 2))}</pre>`,
                wide: true
              });
            }
          });
        }, __("Daftra"));
      }
    },
    validate: calculate_document,
    paid_amount: calculate_document,
    discount_amount: calculate_document
  });

  frappe.ui.form.on("Sales Invoice Item", {
    qty: calculate_document,
    rate: calculate_document,
    vat_rate: calculate_document,
    items_remove: calculate_document
  });

  frappe.ui.form.on("Sales Quotation", {
    refresh(frm) {
      add_print_button(frm);
      if (!frm.is_new()) {
        frm.add_custom_button(__("Create Invoice"), () => {
          frappe.call({
            method: "daftra.api.sales_api.create_invoice_from_quotation",
            args: { quotation_name: frm.doc.name },
            callback(r) { if (r.message) frappe.set_route("Form", "Sales Invoice", r.message); }
          });
        }, __("Daftra"));
      }
    },
    validate: calculate_document
  });

  frappe.ui.form.on("Sales Quotation Item", {
    qty: calculate_document,
    rate: calculate_document,
    vat_rate: calculate_document,
    items_remove: calculate_document
  });

  frappe.ui.form.on("Purchase Invoice", {
    refresh: add_print_button,
    validate: calculate_document,
    paid_amount: calculate_document
  });

  frappe.ui.form.on("Purchase Invoice Item", {
    qty: calculate_document,
    rate: calculate_document,
    vat_rate: calculate_document,
    items_remove: calculate_document
  });

  frappe.ui.form.on("Time Entry", {
    validate(frm) { frm.set_value("billable_amount", money(frm.doc.duration_hours) * money(frm.doc.hourly_rate)); },
    duration_hours(frm) { frm.trigger("validate"); },
    hourly_rate(frm) { frm.trigger("validate"); }
  });

  frappe.ui.form.on("Daftra Settings", {
    refresh(frm) {
      frm.add_custom_button(__("Open Daftra App"), () => window.open("/daftra", "_blank"));
    }
  });
}());
