// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Document Register", {
	effective_from(frm) {
		set_revision_date(frm);
	},

	document_subclass(frm) {
		set_revision_date(frm);
	}
});

function set_revision_date(frm) {
	if (!frm.doc.effective_from || !frm.doc.document_subclass) {
		frm.set_value("revision_date", null);
		return;
	}

	frappe.db.get_value(
		"Document Register Subclass",
		frm.doc.document_subclass,
		"valid_for"
	).then((r) => {
		const valid_for = parseInt(r.message?.valid_for || 0, 10);

		if (valid_for <= 0) {
			frm.set_value("revision_date", null);
			return;
		}

		let revision_date = frappe.datetime.add_months(frm.doc.effective_from, valid_for);
		revision_date = frappe.datetime.add_days(revision_date, -1);

		frm.set_value("revision_date", revision_date);
	});
}