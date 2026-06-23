(function () {
  function money(value) {
    return flt(value || 0);
  }

  function today() {
    return frappe.datetime ? frappe.datetime.get_today() : new Date().toISOString().slice(0, 10);
  }

  function bankBasedMethod(method) {
    return ["Bank Transfer", "Card", "Online"].includes(method);
  }

  function addDays(dateValue, days) {
    if (!days) return dateValue;
    return frappe.datetime.add_days(dateValue || today(), days);
  }

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
    if (frm.doc.total !== undefined) frm.set_value("total", subtotal - money(frm.doc.discount_amount) - money(frm.doc.deposit_amount) + money(frm.doc.adjustment_amount) + tax);
    if (frm.doc.balance !== undefined) frm.set_value("balance", money(frm.doc.total) - money(frm.doc.paid_amount));
    frm.refresh_field("items");
  }

  function add_print_button(frm) {
    if (!frm.is_new()) {
      frm.add_custom_button(__("Preview Print"), () => frappe.set_route("print", frm.doc.doctype, frm.doc.name), __("Daftra"));
    }
  }

  function add_common_invoice_actions(frm) {
    add_print_button(frm);
    if (frm.is_new()) return;

    frm.add_custom_button(__("Record Payment"), () => {
      frappe.new_doc("Invoice Payment", {
        sales_invoice: frm.doc.name,
        client: frm.doc.client,
        amount: frm.doc.balance || frm.doc.total || 0,
      });
    }, __("Daftra"));

    frm.add_custom_button(__("Fill from Client"), () => {
      if (frm.doc.client) frm.trigger("client");
    }, __("Daftra"));

    frm.add_custom_button(__("Check ZATCA"), () => {
      frappe.call({
        method: "daftra.api.zatca_api.validate_zatca_invoice",
        args: { invoice_name: frm.doc.name },
        callback(r) {
          const data = r.message || {};
          frappe.msgprint({
            title: __("ZATCA Validation"),
            message: `<div>${(data.errors || []).map((item) => `<div class="text-danger">${frappe.utils.escape_html(item)}</div>`).join("")}${(data.warnings || []).map((item) => `<div class="text-warning">${frappe.utils.escape_html(item)}</div>`).join("") || (!data.errors?.length ? `<div class="text-success">${__("Invoice looks good for ZATCA")}</div>` : "")}</div>`,
            wide: true,
          });
        },
      });
    }, __("Daftra"));

    frm.add_custom_button(__("ZATCA QR"), () => {
      frappe.call({
        method: "daftra.api.zatca_api.get_zatca_qr",
        args: { invoice_name: frm.doc.name },
        callback(r) {
          const payload = r.message || {};
          frappe.msgprint({
            title: __("ZATCA QR Data"),
            message: `<pre>${frappe.utils.escape_html(JSON.stringify(payload, null, 2))}</pre>`,
            wide: true,
          });
        },
      });
    }, __("Daftra"));
  }

  function autofill_client(frm) {
    if (!frm.doc.client) return;
    frappe.db.get_value("Client", frm.doc.client, [
      "client_type",
      "business_name",
      "first_name",
      "last_name",
      "email",
      "phone",
      "mobile",
      "city",
      "country",
      "tax_id",
      "cr_number",
      "credit_period",
      "credit_limit",
    ], (r) => {
      if (!r) return;
      if (!frm.doc.payment_terms_days && r.credit_period) {
        frm.set_value("payment_terms_days", r.credit_period);
      }
      if (!frm.doc.work_ordered_by && r.business_name) {
        frm.set_value("work_ordered_by", r.business_name);
      }
      if (!frm.doc.notes && r.client_type === "Business") {
        frm.set_value("notes", `${r.business_name || r.first_name || "Client"} · ${r.country || ""}`.trim());
      }
      if (!frm.doc.due_date && frm.doc.invoice_date && r.credit_period) {
        frm.set_value("due_date", addDays(frm.doc.invoice_date, r.credit_period));
      }
      frm.refresh_fields(["payment_terms_days", "due_date", "work_ordered_by", "notes"]);
    });
  }

  function autofill_product(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row.item) return;
    frappe.db.get_value("Product", row.item, [
      "product_name",
      "description",
      "selling_price",
      "purchase_price",
      "vat_rate",
      "unit_of_measure",
      "product_type",
    ], (r) => {
      if (!r) return;
      if (!row.description) {
        frappe.model.set_value(cdt, cdn, "description", r.description || r.product_name || row.item);
      }
      if (!row.rate) {
        frappe.model.set_value(cdt, cdn, "rate", money(r.selling_price || r.purchase_price));
      }
      if (!row.vat_rate) {
        frappe.model.set_value(cdt, cdn, "vat_rate", money(r.vat_rate));
      }
      if (r.product_type === "Service" && !row.qty) {
        frappe.model.set_value(cdt, cdn, "qty", 1);
      }
      frm.trigger("validate");
    });
  }

  function validate_invoice(frm) {
    if (!frm.doc.client) {
      frappe.throw(__("Client is required"));
    }
    if (!frm.doc.items || !frm.doc.items.length) {
      frappe.throw(__("At least one item is required"));
    }
    if (frm.doc.invoice_date && frm.doc.due_date && frm.doc.due_date < frm.doc.invoice_date) {
      frappe.throw(__("Due Date cannot be before Invoice Date"));
    }
    let hasPositive = false;
    (frm.doc.items || []).forEach((row, index) => {
      if (money(row.qty) <= 0) {
        frappe.throw(__("Row {0}: quantity must be greater than zero", [index + 1]));
      }
      if (money(row.rate) < 0) {
        frappe.throw(__("Row {0}: rate cannot be negative", [index + 1]));
      }
      if (money(row.amount) > 0) hasPositive = true;
    });
    if (!hasPositive) {
      frappe.throw(__("Invoice total must be greater than zero"));
    }
    if (frm.doc.invoice_layout === "Materials & Services" && !frm.doc.description_of_work) {
      frappe.throw(__("Description of Work is required for Materials & Services layouts"));
    }
  }

  frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
      add_common_invoice_actions(frm);
    },
    client(frm) {
      autofill_client(frm);
    },
    invoice_date(frm) {
      if (frm.doc.payment_terms_days && !frm.doc.due_date) {
        frm.set_value("due_date", addDays(frm.doc.invoice_date, frm.doc.payment_terms_days));
      }
    },
    validate(frm) {
      calculate_document(frm);
      validate_invoice(frm);
    },
    paid_amount: calculate_document,
    discount_amount: calculate_document,
    deposit_amount: calculate_document,
    adjustment_amount: calculate_document,
  });

  frappe.ui.form.on("Sales Invoice Item", {
    item(frm, cdt, cdn) {
      autofill_product(frm, cdt, cdn);
    },
    qty(frm) {
      calculate_document(frm);
    },
    rate(frm) {
      calculate_document(frm);
    },
    vat_rate(frm) {
      calculate_document(frm);
    },
    items_remove(frm) {
      calculate_document(frm);
    },
  });

  frappe.ui.form.on("Sales Quotation", {
    refresh(frm) {
      add_print_button(frm);
      if (!frm.is_new()) {
        frm.add_custom_button(__("Create Invoice"), () => {
          frappe.call({
            method: "daftra.api.sales_api.create_invoice_from_quotation",
            args: { quotation_name: frm.doc.name },
            callback(r) {
              if (r.message) frappe.set_route("Form", "Sales Invoice", r.message);
            },
          });
        }, __("Daftra"));
      }
    },
    client: autofill_client,
    validate(frm) {
      calculate_document(frm);
    },
  });

  frappe.ui.form.on("Sales Quotation Item", {
    item(frm, cdt, cdn) {
      autofill_product(frm, cdt, cdn);
    },
    qty(frm) {
      calculate_document(frm);
    },
    rate(frm) {
      calculate_document(frm);
    },
    vat_rate(frm) {
      calculate_document(frm);
    },
    items_remove(frm) {
      calculate_document(frm);
    },
  });

  frappe.ui.form.on("Purchase Invoice", {
    refresh(frm) {
      add_print_button(frm);
    },
    supplier(frm) {
      if (!frm.doc.supplier) return;
      frappe.db.get_value("Supplier", frm.doc.supplier, ["payment_terms"], (r) => {
        const terms = r && r.payment_terms ? parseInt(String(r.payment_terms).match(/\d+/)?.[0] || "0", 10) : 0;
        if (terms && !frm.doc.payment_terms_days) {
          frm.set_value("payment_terms_days", terms);
        }
        if (terms && frm.doc.invoice_date && !frm.doc.due_date) {
          frm.set_value("due_date", addDays(frm.doc.invoice_date, terms));
        }
      });
    },
    validate(frm) {
      calculate_document(frm);
      if (!frm.doc.supplier) {
        frappe.throw({ message: __("Supplier is required") });
      }
    },
    paid_amount: calculate_document,
  });

  frappe.ui.form.on("Purchase Invoice Item", {
    item(frm, cdt, cdn) {
      autofill_product(frm, cdt, cdn);
    },
    qty(frm) {
      calculate_document(frm);
    },
    rate(frm) {
      calculate_document(frm);
    },
    vat_rate(frm) {
      calculate_document(frm);
    },
    items_remove(frm) {
      calculate_document(frm);
    },
  });

  frappe.ui.form.on("Time Entry", {
    validate(frm) {
      frm.set_value("billable_amount", money(frm.doc.duration_hours) * money(frm.doc.hourly_rate));
    },
    duration_hours(frm) {
      frm.trigger("validate");
    },
    hourly_rate(frm) {
      frm.trigger("validate");
    },
  });


  function paymentBankToggle(frm) {
    const needsBank = bankBasedMethod(frm.doc.payment_method);
    frm.set_df_property("bank_registration", "reqd", needsBank ? 1 : 0);
    frm.set_df_property("bank_registration", "hidden", needsBank ? 0 : 1);
    frm.refresh_fields(["bank_registration", "treasury"]);
  }

  function syncPaymentBank(frm) {
    paymentBankToggle(frm);
    if (!frm.doc.bank_registration) return;
    frappe.db.get_value("Bank Registration", frm.doc.bank_registration, ["linked_treasury"], (r) => {
      if (r && r.linked_treasury) {
        frm.set_value("treasury", r.linked_treasury);
      }
    });
  }

  frappe.ui.form.on("Daftra Settings", {
    refresh(frm) {
      frm.add_custom_button(__("Open Daftra App"), () => window.open("/daftra", "_blank"));
    },
  });

  ["Invoice Payment", "Supplier Payment"].forEach((doctype) => {
    frappe.ui.form.on(doctype, {
      refresh(frm) {
        paymentBankToggle(frm);
      },
      payment_method(frm) {
        if (!bankBasedMethod(frm.doc.payment_method)) {
          frm.set_value("bank_registration", null);
        }
        paymentBankToggle(frm);
      },
      bank_registration(frm) {
        syncPaymentBank(frm);
      },
    });
  });

}());
