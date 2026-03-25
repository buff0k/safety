// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Meeting Manager", {
  refresh(frm) {
    maybe_set_unique_number(frm);
  },

  datetime_of_meeting_end(frm) {
    maybe_set_unique_number(frm);
  }
});

async function maybe_set_unique_number(frm) {
  if (!frm.doc.datetime_of_meeting_end) {
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
      method: "safety.safety.doctype.meeting_manager.meeting_manager.get_next_unique_number_preview",
      args: {
        datetime_of_meeting_end: frm.doc.datetime_of_meeting_end
      }
    });

    if (r.message) {
      await frm.set_value("unique_number", r.message);
    }
  } catch (e) {
    console.error("Failed to generate Meeting Manager unique number preview", e);
  }
}