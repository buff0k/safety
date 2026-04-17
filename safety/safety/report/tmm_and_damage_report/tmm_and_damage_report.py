import frappe
from frappe import _


INCIDENT_DOCTYPE = "Incident Report"
EQUIPMENT_CHILD_DOCTYPE = "Equipment"
INCIDENT_TYPE_CHILD_DOCTYPE = "Classify Type of Incident"
DAMAGE_TYPE_CHILD_DOCTYPE = "Equipment Damage Type"


def execute(filters=None):
	filters = frappe._dict(filters or {})

	validate_filters(filters)

	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def validate_filters(filters):
	if filters.get("start_date") and filters.get("end_date"):
		if filters.start_date > filters.end_date:
			frappe.throw(_("Start Date cannot be after End Date."))


def get_columns():
	return [
		{
			"label": _("Equipment ID"),
			"fieldname": "equipment_id",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Damage Entries"),
			"fieldname": "damage_entry_count",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": _("Incident Count"),
			"fieldname": "incident_count",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": _("Total Cost"),
			"fieldname": "total_cost",
			"fieldtype": "Currency",
			"width": 160,
		},
	]


def get_data(filters):
	conditions = []
	params = {}

	conditions.append("ir.docstatus < 2")

	if filters.get("start_date"):
		conditions.append("DATE(ir.datetime_incident) >= %(start_date)s")
		params["start_date"] = filters.get("start_date")

	if filters.get("end_date"):
		conditions.append("DATE(ir.datetime_incident) <= %(end_date)s")
		params["end_date"] = filters.get("end_date")

	select_type_of_incident = normalize_filter_value(filters.get("select_type_of_incident"))
	if select_type_of_incident:
		params["select_type_of_incident"] = select_type_of_incident
		conditions.append(
			build_table_multiselect_condition(
				parentfield="select_type_of_incident",
				child_doctype=INCIDENT_TYPE_CHILD_DOCTYPE,
				filter_param="select_type_of_incident",
			)
		)

	type_of_damage = normalize_filter_value(filters.get("type_of_damage"))
	if type_of_damage:
		params["type_of_damage"] = type_of_damage
		conditions.append(
			build_table_multiselect_condition(
				parentfield="type_of_damage",
				child_doctype=DAMAGE_TYPE_CHILD_DOCTYPE,
				filter_param="type_of_damage",
			)
		)

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			COALESCE(eq.equipment_id, 'Unknown') AS equipment_id,
			COUNT(eq.name) AS damage_entry_count,
			COUNT(DISTINCT ir.name) AS incident_count,
			SUM(COALESCE(eq.value_of_the_damage, 0)) AS total_cost
		FROM `tab{INCIDENT_DOCTYPE}` ir
		INNER JOIN `tab{EQUIPMENT_CHILD_DOCTYPE}` eq
			ON eq.parent = ir.name
			AND eq.parenttype = %(incident_parenttype)s
			AND eq.parentfield = %(equipment_parentfield)s
		WHERE {where_clause}
		GROUP BY COALESCE(eq.equipment_id, 'Unknown')
		ORDER BY total_cost DESC, equipment_id ASC
	"""

	params["incident_parenttype"] = INCIDENT_DOCTYPE
	params["equipment_parentfield"] = "equipment_details"

	return frappe.db.sql(query, params, as_dict=True)


def build_table_multiselect_condition(parentfield, child_doctype, filter_param):
	link_field = get_first_link_field(child_doctype)

	if link_field:
		value_field = f"child.`{link_field}`"
	else:
		# Fallback in case the child doctype has no Link field
		value_field = "child.name"

	return f"""
		EXISTS (
			SELECT 1
			FROM `tab{child_doctype}` child
			WHERE child.parent = ir.name
				AND child.parenttype = '{INCIDENT_DOCTYPE}'
				AND child.parentfield = '{parentfield}'
				AND {value_field} = %({filter_param})s
		)
	"""


def get_first_link_field(child_doctype):
	meta = frappe.get_meta(child_doctype)

	for df in meta.fields:
		if df.fieldtype == "Link":
			return df.fieldname

	return None


def normalize_filter_value(value):
	if isinstance(value, (list, tuple)):
		return value[0] if value else None

	if isinstance(value, str):
		value = value.strip()
		return value or None

	return value


def get_chart(data):
	if not data:
		return None

	labels = [row.get("equipment_id") for row in data[:10]]
	values = [flt(row.get("total_cost")) for row in data[:10]]

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Total Cost",
					"values": values,
				}
			],
		},
		"type": "bar",
		"height": 300,
	}


def get_report_summary(data):
	total_cost = sum(flt(row.get("total_cost")) for row in data)
	total_damage_entries = sum(cint(row.get("damage_entry_count")) for row in data)
	total_incidents = sum(cint(row.get("incident_count")) for row in data)

	return [
		{
			"value": total_cost,
			"label": _("Grand Total Cost"),
			"indicator": "Red",
			"datatype": "Currency",
		},
		{
			"value": total_damage_entries,
			"label": _("Total Damage Entries"),
			"indicator": "Blue",
			"datatype": "Int",
		},
		{
			"value": total_incidents,
			"label": _("Total Incidents"),
			"indicator": "Green",
			"datatype": "Int",
		},
	]


def flt(value):
	try:
		return float(value or 0)
	except Exception:
		return 0.0


def cint(value):
	try:
		return int(value or 0)
	except Exception:
		return 0