// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("RMA", {
  refresh(frm) {
    maybe_set_unique_number(frm);
  },

  date(frm) {
    maybe_set_unique_number(frm);
  },

  incident_number(frm) {
    maybe_set_unique_number(frm);
  }
});

async function maybe_set_unique_number(frm) {
  if (!frm.doc.date || !frm.doc.incident_number) {
    if (frm.is_new()) {
      await frm.set_value("unique_number", "");
    }
    return;
  }

  if (!frm.is_new() && frm.doc.unique_number) {
    return;
  }

  try {
    const r = await frappe.call({
      method: "safety.safety.doctype.rma.rma.get_next_unique_number_preview",
      args: {
        date: frm.doc.date
      }
    });

    if (r.message) {
      await frm.set_value("unique_number", r.message);
    }
  } catch (e) {
    console.error("Failed to generate RMA unique number preview", e);
  }
}