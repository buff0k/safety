// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Incident Investigation Interview", {
    refresh(frm) {
        toggle_interviewee_fields(frm);
    },

    external_interviewee(frm) {
        toggle_interviewee_fields(frm);
    },

    interviewee_employee(frm) {
        if (!frm.doc.interviewee_employee) {
            return;
        }

        frappe.db.get_value(
            "Employee",
            frm.doc.interviewee_employee,
            ["employee_name", "designation"]
        ).then((r) => {
            const employee = r.message || {};
            frm.set_value("interviewee_designation", employee.designation);
        });
    },
});

function toggle_interviewee_fields(frm) {
    const external = Boolean(frm.doc.external_interviewee);
    frm.toggle_display("interviewee_employee", !external);
    frm.toggle_reqd("interviewee_employee", !external);
    frm.toggle_display("external_interviewee_name", external);
    frm.toggle_reqd("external_interviewee_name", external);
}
