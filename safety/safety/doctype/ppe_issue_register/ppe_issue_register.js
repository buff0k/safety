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
	},

	issue_date(frm) {
		set_reissue_dates_from_issue_date(frm);
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
				child.re_issue_date = get_reissue_date(frm.doc.issue_date);
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

function set_reissue_dates_from_issue_date(frm) {
	if (!frm.doc.issue_date || !frm.doc.ppe_issued || !frm.doc.ppe_issued.length) {
		return;
	}

	const reissue_date = get_reissue_date(frm.doc.issue_date);

	(frm.doc.ppe_issued || []).forEach((row) => {
		row.re_issue_date = reissue_date;
	});

	frm.refresh_field("ppe_issued");
}

function get_reissue_date(issue_date) {
	if (!issue_date) {
		return "";
	}

	let reissue_date = frappe.datetime.add_months(issue_date, 12);
	reissue_date = frappe.datetime.add_days(reissue_date, -1);

	return reissue_date;
}