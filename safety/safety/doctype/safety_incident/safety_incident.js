// Copyright (c) 2025, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Safety Incident", {
    safetyemployee: function(frm) {
        if (frm.doc.safetyemployee) {
            frappe.call({
                method: 'safety.safety.doctype.safety_incident.safety_incident.fetch_employee_data',
                args: {
                    employee_id: frm.doc.safetyemployee
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('safetyfull_name', r.message.employee_name);
                        frm.set_value('safetydesignation', r.message.designation);
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
            frappe.call({
                method: 'safety.safety.doctype.safety_incident.safety_incident.fetch_employee_data',
                args: {
                    employee_id: row.employee
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'employee_name', r.message.employee_name);
                        frappe.model.set_value(cdt, cdn, 'designation', r.message.designation);
                    }
                }
            });
        }
    }
});

frappe.ui.form.on('Safety Incident Equipment', {
    asset: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.asset) {
            frappe.call({
                method: 'safety.safety.doctype.safety_incident.safety_incident.fetch_asset_data',
                args: {
                    asset_id: row.asset
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'asset_name', r.message.asset_name);
                        frappe.model.set_value(cdt, cdn, 'asset_category', r.message.asset_category);
                    }
                }
            });
        }
    }
});