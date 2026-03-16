frappe.query_reports["Incident Analysis Master Report"] = {
	onload: function (report) {
		toggle_specialist_filters(report);
	},

	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.year_start(),
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.year_end(),
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "site",
			label: __("Site"),
			fieldtype: "Link",
			options: "Branch",
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "region",
			label: __("Region"),
			fieldtype: "Link",
			options: "Area Setup",
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "departmentx",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "shift",
			label: __("Shift"),
			fieldtype: "Select",
			options: "\nDay 1\nDay 2\nDay 3\nNight 1\nNight 2\nNight 3",
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "report_mode",
			label: __("Report Mode"),
			fieldtype: "Select",
			reqd: 1,
			default: "Nature of Injury",
			options: "\nNature of Injury\nType of Damage\nBody Part\nTask\nShift Summary\nDay of Week\nDay of Month\nHour of Day\nIncident Type\nSeverity",
			on_change: function (report) {
				toggle_specialist_filters(frappe.query_report);
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "layout",
			label: __("Layout"),
			fieldtype: "Select",
			reqd: 1,
			default: "Summary",
			options: "\nSummary\nMonthly\nYearly\nMatrix",
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "nature_of_injury_filter",
			label: __("Nature of Injury"),
			fieldtype: "Link",
			options: "Nature of Injury",
			hidden: 0,
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "type_of_damage_filter",
			label: __("Type of Damage"),
			fieldtype: "Link",
			options: "Equipment Damage Type",
			hidden: 1,
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "body_part_filter",
			label: __("Body Part"),
			fieldtype: "Link",
			options: "Body Part",
			hidden: 1,
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "task_filter",
			label: __("Task"),
			fieldtype: "Link",
			options: "Task Classify",
			hidden: 1,
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "severity_filter",
			label: __("Severity"),
			fieldtype: "Link",
			options: "Safety Incident Severity Classification",
			hidden: 1,
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
	],
};

function toggle_specialist_filters(report) {
	const mode = report.get_filter_value("report_mode");

	const visibility = {
		nature_of_injury_filter: mode === "Nature of Injury",
		type_of_damage_filter: mode === "Type of Damage",
		body_part_filter: mode === "Body Part",
		task_filter: mode === "Task",
		severity_filter: mode === "Severity",
	};

	Object.keys(visibility).forEach((fieldname) => {
		report.toggle_filter_display(fieldname, visibility[fieldname]);

		if (!visibility[fieldname]) {
			report.set_filter_value(fieldname, "");
		}
	});
}