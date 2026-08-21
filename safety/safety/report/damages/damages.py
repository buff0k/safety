import frappe
from frappe import _


PARENT_DOCTYPE = "PPE Issue Register"
CHILD_DOCTYPE = "PPE Issue Register Table"
CHILD_PARENTFIELD = "ppe_issued"

STATUS_FIELD = "re_issue_ahead_of_re_issue_date"


def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 190,
		},
		{
			"label": _("Site"),
			"fieldname": "site",
			"fieldtype": "Link",
			"options": "Location",
			"width": 160,
		},
		{
			"label": _("PPE Item"),
			"fieldname": "ppe_item",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Issue Date"),
			"fieldname": "issue_day",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Re-Issue Date"),
			"fieldname": "re_issue_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Reason"),
			"fieldname": "reason",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("PPE Issue Register"),
			"fieldname": "ppe_issue_register",
			"fieldtype": "Link",
			"options": PARENT_DOCTYPE,
			"width": 160,
		},
	]


def get_data(filters):
	parent_meta = frappe.get_meta(PARENT_DOCTYPE)
	child_meta = frappe.get_meta(CHILD_DOCTYPE)

	if not child_meta.has_field(STATUS_FIELD):
		frappe.throw(
			_(
				"Field {0} was not found in {1}."
			).format(
				frappe.bold(STATUS_FIELD),
				frappe.bold(CHILD_DOCTYPE),
			)
		)

	# ---------------------------------------------------------
	# Identify the relevant fields safely from the DocType meta
	# ---------------------------------------------------------

	site_field = get_first_existing_field(
		parent_meta,
		[
			"site",
			"location",
		],
	)

	issue_date_field = get_first_existing_field(
		child_meta,
		[
			"issue_day",
			"issue_date",
		],
	)

	re_issue_date_field = get_first_existing_field(
		child_meta,
		[
			"re_issue_date",
			"reissue_date",
		],
	)

	ppe_item_field = get_first_existing_field(
		child_meta,
		[
			"ppe_item",
			"ppe",
			"ppe_type",
			"item",
			"item_code",
			"description",
			"ppe_description",
		],
	)

	# ---------------------------------------------------------
	# Build SELECT expressions
	# ---------------------------------------------------------

	site_select = (
		f"parent.`{site_field}`"
		if site_field
		else "''"
	)

	issue_date_select = (
		f"child.`{issue_date_field}`"
		if issue_date_field
		else "NULL"
	)

	re_issue_date_select = (
		f"child.`{re_issue_date_field}`"
		if re_issue_date_field
		else "NULL"
	)

	ppe_item_select = (
		f"child.`{ppe_item_field}`"
		if ppe_item_field
		else "''"
	)

	# ---------------------------------------------------------
	# Conditions
	# ---------------------------------------------------------

	conditions = [
		"child.parenttype = %(parenttype)s",
		"child.parentfield = %(parentfield)s",
		f"child.`{STATUS_FIELD}` IN ('Lost', 'Damaged')",
	]

	values = {
		"parenttype": PARENT_DOCTYPE,
		"parentfield": CHILD_PARENTFIELD,
	}

	# ---------------------------------------------------------
	# Optional Lost / Damaged filter
	# ---------------------------------------------------------

	if filters.get("reason") in ("Lost", "Damaged"):
		conditions.append(
			f"child.`{STATUS_FIELD}` = %(reason)s"
		)
		values["reason"] = filters.reason

	# ---------------------------------------------------------
	# Optional date filters
	#
	# These currently use issue_day / issue_date.
	# ---------------------------------------------------------

	if filters.get("start_date"):
		if not issue_date_field:
			frappe.throw(
				_(
					"Start Date cannot be used because no issue date "
					"field was found in PPE Issue Register Table."
				)
			)

		conditions.append(
			f"child.`{issue_date_field}` >= %(start_date)s"
		)
		values["start_date"] = filters.start_date

	if filters.get("end_date"):
		if not issue_date_field:
			frappe.throw(
				_(
					"End Date cannot be used because no issue date "
					"field was found in PPE Issue Register Table."
				)
			)

		conditions.append(
			f"child.`{issue_date_field}` <= %(end_date)s"
		)
		values["end_date"] = filters.end_date

	# ---------------------------------------------------------
	# Optional Site / Location filter
	# ---------------------------------------------------------

	if filters.get("site"):
		if not site_field:
			frappe.throw(
				_(
					"Site filter was selected, but a site/location "
					"field could not be found on PPE Issue Register."
				)
			)

		conditions.append(
			f"parent.`{site_field}` = %(site)s"
		)
		values["site"] = filters.site

	where_clause = " AND ".join(conditions)

	# ---------------------------------------------------------
	# Sorting
	# ---------------------------------------------------------

	if issue_date_field:
		order_by = (
			f"child.`{issue_date_field}` DESC, "
			"parent.employee_name ASC"
		)
	else:
		order_by = (
			"parent.modified DESC, "
			"parent.employee_name ASC"
		)

	# ---------------------------------------------------------
	# Main query
	# ---------------------------------------------------------

	query = f"""
		SELECT
			parent.name AS ppe_issue_register,
			parent.employee AS employee,
			parent.employee_name AS employee_name,

			{site_select} AS site,
			{ppe_item_select} AS ppe_item,
			{issue_date_select} AS issue_day,
			{re_issue_date_select} AS re_issue_date,

			child.`{STATUS_FIELD}` AS reason

		FROM `tab{CHILD_DOCTYPE}` child

		INNER JOIN `tab{PARENT_DOCTYPE}` parent
			ON parent.name = child.parent

		WHERE
			{where_clause}

		ORDER BY
			{order_by}
	"""

	return frappe.db.sql(
		query,
		values,
		as_dict=True,
	)


def get_chart(data):
	lost_count = 0
	damaged_count = 0

	for row in data:
		reason = (row.get("reason") or "").strip()

		if reason == "Lost":
			lost_count += 1

		elif reason == "Damaged":
			damaged_count += 1

	return {
		"data": {
			"labels": [
				_("Lost"),
				_("Damaged"),
			],
			"datasets": [
				{
					"name": _("PPE Records"),
					"values": [
						lost_count,
						damaged_count,
					],
				}
			],
		},
		"type": "bar",
		"height": 260,
		"colors": [
			"#e74c3c",
		],
	}


def get_report_summary(data):
	lost_count = 0
	damaged_count = 0

	for row in data:
		reason = (row.get("reason") or "").strip()

		if reason == "Lost":
			lost_count += 1

		elif reason == "Damaged":
			damaged_count += 1

	total = lost_count + damaged_count

	return [
		{
			"value": total,
			"indicator": "Blue",
			"label": _("Total Records"),
			"datatype": "Int",
		},
		{
			"value": lost_count,
			"indicator": "Orange",
			"label": _("Lost"),
			"datatype": "Int",
		},
		{
			"value": damaged_count,
			"indicator": "Red",
			"label": _("Damaged"),
			"datatype": "Int",
		},
	]


def get_first_existing_field(meta, possible_fields):
	"""
	Return the first fieldname that exists on the supplied DocType.
	This allows the report to tolerate small field naming differences.
	"""

	for fieldname in possible_fields:
		if meta.has_field(fieldname):
			return fieldname

	return None