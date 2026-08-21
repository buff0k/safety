frappe.query_reports["Damages"] = {
	filters: [
		{
			fieldname: "start_date",
			label: __("Start Date"),
			fieldtype: "Date",
			on_change: function () {
				validate_dates_and_refresh();
			}
		},
		{
			fieldname: "end_date",
			label: __("End Date"),
			fieldtype: "Date",
			on_change: function () {
				validate_dates_and_refresh();
			}
		},
		{
			fieldname: "site",
			label: __("Site"),
			fieldtype: "Link",
			options: "Location",
			on_change: function () {
				frappe.query_report.refresh();
			}
		},
		{
			fieldname: "reason",
			label: __("Lost / Damaged"),
			fieldtype: "Select",
			options: [
				"",
				"Lost",
				"Damaged"
			],
			on_change: function () {
				frappe.query_report.refresh();
			}
		}
	],

	onload: function (report) {
		// No mandatory filters.
		// Opening the report therefore immediately returns
		// both Lost and Damaged PPE records.
	}
};


function validate_dates_and_refresh() {
	const start_date = frappe.query_report.get_filter_value("start_date");
	const end_date = frappe.query_report.get_filter_value("end_date");

	if (start_date && end_date && start_date > end_date) {
		frappe.msgprint({
			title: __("Invalid Date Range"),
			message: __("Start Date cannot be later than End Date."),
			indicator: "red"
		});

		return;
	}

	frappe.query_report.refresh();
}