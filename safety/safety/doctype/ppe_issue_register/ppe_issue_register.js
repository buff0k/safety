// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("PPE Issue Register", {
	employee(frm) {
		if (!frm.doc.employee) {
			frm.set_value("employee_name", "");
			frm.set_value("branch", "");
			frm.set_value("designation", "");
			frm.set_value("company", "");
			frm.set_value("letter_head", "");
			frm.clear_table("ppe_issued");
			frm.refresh_field("ppe_issued");
			return;
		}

		frappe.db.get_value(
			"Employee",
			frm.doc.employee,
			["employee_name", "branch", "designation", "company"]
		).then((r) => {
			if (r.message) {
				frm.set_value("employee_name", r.message.employee_name || "");
				frm.set_value("branch", r.message.branch || "");
				frm.set_value("designation", r.message.designation || "");
				frm.set_value("company", r.message.company || "");

				if (r.message.company) {
					set_default_letter_head(frm, r.message.company);
				} else {
					frm.set_value("letter_head", "");
				}

				if (r.message.designation) {
					populate_ppe_from_designation(frm, r.message.designation);
				} else {
					frm.clear_table("ppe_issued");
					frm.refresh_field("ppe_issued");
				}
			}
		});
	},

	designation(frm) {
		if (frm.doc.designation) {
			populate_ppe_from_designation(frm, frm.doc.designation);
		} else {
			frm.clear_table("ppe_issued");
			frm.refresh_field("ppe_issued");
		}
	},

	company(frm) {
		if (frm.doc.company) {
			set_default_letter_head(frm, frm.doc.company);
		} else {
			frm.set_value("letter_head", "");
		}
	}
});

frappe.ui.form.on("PPE Issue Register Table", {
	issue_day(frm, cdt, cdn) {
		set_child_reissue_date(cdt, cdn);
	},

	date_of_re_issue(frm, cdt, cdn) {
		set_child_reissue_date(cdt, cdn);
	},

	ppe_issued_add(frm, cdt, cdn) {
		set_child_reissue_date(cdt, cdn);
	}
});

function populate_ppe_from_designation(frm, designation) {
	frappe.db.get_doc("PPE Per Designation", designation)
		.then((doc) => {
			frm.clear_table("ppe_issued");

			(doc.ppe_required || []).forEach((row) => {
				let child = frm.add_child("ppe_issued");
				child.item = row.item;
				child.qty = row.qty;

				// Re-Issue Date is calculated from child issue_day first.
				// If issue_day is empty, it falls back to child date_of_re_issue.
				child.re_issue_date = get_reissue_date_from_child_row(child);
			});

			frm.refresh_field("ppe_issued");
		})
		.catch(() => {
			frm.clear_table("ppe_issued");
			frm.refresh_field("ppe_issued");

			frappe.show_alert({
				message: __("No PPE Per Designation record found for designation: {0}", [designation]),
				indicator: "orange"
			});
		});
}

function set_default_letter_head(frm, company) {
	frappe.db.get_value("Company", company, "default_letter_head")
		.then((r) => {
			frm.set_value("letter_head", (r.message && r.message.default_letter_head) || "");
		});
}

function set_child_reissue_date(cdt, cdn) {
	let row = locals[cdt][cdn];

	if (!row) {
		return;
	}

	let reissue_date = get_reissue_date_from_child_row(row);

	frappe.model.set_value(cdt, cdn, "re_issue_date", reissue_date);
}

function get_reissue_date_from_child_row(row) {
	if (!row) {
		return "";
	}

	let source_date = row.issue_day || row.date_of_re_issue;

	return get_reissue_date(source_date);
}

function get_reissue_date(source_date) {
	if (!source_date) {
		return "";
	}

	let reissue_date = frappe.datetime.add_months(source_date, 12);
	reissue_date = frappe.datetime.add_days(reissue_date, -1);

	return reissue_date;
}