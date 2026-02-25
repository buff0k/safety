// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Emergency Preparedness", {
  onload(frm) {
    // If site is already set on a new doc, generate immediately
    if (frm.is_new() && frm.doc.site && !frm.doc.unique_number) {
      frm.trigger("generate_unique_number");
    }
  },

  site(frm) {
    frm.trigger("generate_unique_number");
  },

  generate_unique_number(frm) {
    if (!frm.doc.site) return;

    // Don't override after the document has been saved
    if (!frm.is_new() && frm.doc.unique_number) return;

    // If already generated on this new doc, don't regenerate unless user cleared it
    if (frm.doc.unique_number) return;

    frappe.call({
      method:
        "safety.safety.doctype.emergency_preparedness.emergency_preparedness.get_next_unique_number",
      args: {},
      callback(r) {
        if (!r.exc && r.message) {
          frm.set_value("unique_number", r.message);
        }
      },
    });
  },
});