// Copyright (c) 2025, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Safety Incident", {
    safetyemployee: function(frm) {
        if (frm.doc.safetyemployee) {
            frappe.call({
                method: 'safety.safety.doctype.safety_incident.safety_incident.fetch_safety_data',
                args: {
                    safetyemployee: frm.doc.safetyemployee
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('safetyfull_name', r.message.safetyfull_name);
                        frm.set_value('safetydesignation', r.message.safetydesignation);
                    }
                }
            });
        }
    }
});

frappe.ui.form.on('Safety Incident Employees', {
    employee: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.employee) {
            frappe.db.get_doc('Employee', row.employee).then(employee => {
                frappe.model.set_value(cdt, cdn, 'employee_name', employee.employee_name);
                frappe.model.set_value(cdt, cdn, 'designation', employee.designation);
            });
        }
    }
});

frappe.ui.form.on('Safety Incident Equipment', {
    asset: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.asset) {
            frappe.db.get_doc('Asset', row.asset).then(asset => {
                frappe.model.set_value(cdt, cdn, 'asset_name', asset.asset_name);
                frappe.model.set_value(cdt, cdn, 'asset_category', asset.asset_category);
            });
        }
    }
});