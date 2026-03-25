// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Hazardous Chemical Register", {
  refresh(frm) {
    maybe_set_unique_number(frm);
  },

  last_revision_date(frm) {
    maybe_set_unique_number(frm);
  }
});

async function maybe_set_unique_number(frm) {
  if (!frm.doc.last_revision_date) {
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
      method: "safety.safety.doctype.hazardous_chemical_register.hazardous_chemical_register.get_next_unique_number_preview",
      args: {
        last_revision_date: frm.doc.last_revision_date
      }
    });

    if (r.message) {
      await frm.set_value("unique_number", r.message);
    }
  } catch (e) {
    console.error("Failed to generate Hazardous Chemical Register unique number preview", e);
  }
}