// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Safety Corrective Action", {
    refresh(frm) {
        toggle_effectiveness_fields(frm);
    },

    effectiveness_review_required(frm) {
        toggle_effectiveness_fields(frm);
    },

    responsible_employee(frm) {
        if (!frm.doc.responsible_employee) {
            return;
        }

        frappe.db.get_value(
            "Employee",
            frm.doc.responsible_employee,
            ["user_id", "department"]
        ).then((r) => {
            const employee = r.message || {};
            if (!frm.doc.action_owner) {
                frm.set_value("action_owner", employee.user_id);
            }
            if (!frm.doc.department) {
                frm.set_value("department", employee.department);
            }
        });
    },
});

function toggle_effectiveness_fields(frm) {
    const required = Boolean(frm.doc.effectiveness_review_required);
    frm.toggle_display("effectiveness_review_date", required);
    frm.toggle_reqd("effectiveness_review_date", required);
    frm.toggle_display("effectiveness_result", required);
}
