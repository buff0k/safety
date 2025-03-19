// Copyright (c) 2025, BuFf0k and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Safety Incident", {
// 	refresh(frm) {

// 	},
// });

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