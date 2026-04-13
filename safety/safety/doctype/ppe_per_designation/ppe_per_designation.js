// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("PPE Per Designation Table", {
	item(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (!row.item) {
			frappe.model.set_value(cdt, cdn, "item_name", "");
			return;
		}

		frappe.db.get_value("Item", row.item, "item_name")
			.then((r) => {
				if (r.message) {
					frappe.model.set_value(cdt, cdn, "item_name", r.message.item_name || "");
				}
			});
	}
});