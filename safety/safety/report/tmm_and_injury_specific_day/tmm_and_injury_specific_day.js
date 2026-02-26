// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.query_reports["TMM and Injury Specific Day"] = {
	filters: [
		{
			fieldname: "start_date",
			label: __("Start Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "end_date",
			label: __("End Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "site",
			label: __("Site"),
			fieldtype: "Link",
			options: "Branch",
		},
	],
};