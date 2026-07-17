// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Safety Lessons Learnt", {
    refresh(frm) {
        if (frm.doc.workflow_state === "Published") {
            frm.dashboard.set_headline_alert(
                __("Published on {0}", [frappe.datetime.str_to_user(frm.doc.publication_date)]),
                "green"
            );
        }
    },
});
