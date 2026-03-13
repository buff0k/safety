frappe.ui.form.on("Visible Field Leadership", {
	refresh(frm) {
		if (frm.is_new() && frm.doc.date && !frm.doc.unique_number) {
			set_unique_number(frm);
		}
	},

	date(frm) {
		if (!frm.doc.date) {
			frm.set_value("unique_number", "");
			return;
		}

		set_unique_number(frm);
	}
});

function set_unique_number(frm) {
	if (!frm.doc.date) {
		return;
	}

	frappe.call({
		method: "safety.safety.doctype.visible_field_leadership.visible_field_leadership.get_next_unique_number",
		args: {
			date_value: frm.doc.date,
			docname: frm.doc.name || null
		},
		callback: function (r) {
			if (r.message) {
				frm.set_value("unique_number", r.message);
			}
		}
	});
}