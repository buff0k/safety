// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Incident Investigation Interview", {
    refresh(frm) {
        if (frm.doc.docstatus === 0 && !frm.doc.statement_file) {
            frm.dashboard.set_headline_alert(
                __("Attach the signed interview statement before submitting."),
                "orange"
            );
        }
    }
});