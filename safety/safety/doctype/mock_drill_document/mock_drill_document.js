frappe.ui.form.on("DrillDocumentMockDoc", {
  onload(frm) {
    // If date already set on a new doc, generate immediately
    if (frm.is_new() && frm.doc.date && !frm.doc.unique_drill_document_number) {
      frm.trigger("generate_unique_drill_document_number");
    }
  },

  date(frm) {
    frm.trigger("generate_unique_drill_document_number");
  },

  generate_unique_drill_document_number(frm) {
    if (!frm.doc.date) return;

    // Don't override an existing number once saved
    if (!frm.is_new() && frm.doc.unique_drill_document_number) return;

    // If already set on a new doc, keep it unless user cleared it
    if (frm.doc.unique_drill_document_number) return;

    frappe.call({
      method:
        "your_app.your_module.doctype.drill_document_mock_doc.drill_document_mock_doc.get_next_unique_drill_document_number",
      args: {
        doc_date: frm.doc.date,
      },
      callback(r) {
        if (!r.exc && r.message) {
          frm.set_value("unique_drill_document_number", r.message);
        }
      },
    });
  },
});