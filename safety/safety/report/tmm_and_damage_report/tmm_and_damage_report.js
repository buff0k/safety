frappe.query_reports["TMM and Damage Report"] = {
	filters: [
		{
			fieldname: "start_date",
			label: __("Start Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "end_date",
			label: __("End Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "site",
			label: __("Site"),
			fieldtype: "Link",
			options: "Branch"
		},
		{
			fieldname: "select_type_of_incident",
			label: __("Select Type Of Incident"),
			fieldtype: "Link",
			options: "Classify Type of Incident"
		},
		{
			fieldname: "type_of_damage",
			label: __("Damage Type"),
			fieldtype: "Link",
			options: "Equipment Damage Type"
		}
	]
};