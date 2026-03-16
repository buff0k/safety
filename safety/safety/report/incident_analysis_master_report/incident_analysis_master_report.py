from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

import frappe
from frappe import _
from frappe.utils import getdate


MONTHS = [
	("Jan", 1),
	("Feb", 2),
	("Mar", 3),
	("Apr", 4),
	("May", 5),
	("Jun", 6),
	("Jul", 7),
	("Aug", 8),
	("Sep", 9),
	("Oct", 10),
	("Nov", 11),
	("Dec", 12),
]

DOW_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

SHIFT_ORDER = ["Day 1", "Day 2", "Day 3", "Night 1", "Night 2", "Night 3"]

SYSTEM_CHILD_FIELDS = {
	"name",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"docstatus",
	"idx",
	"parent",
	"parentfield",
	"parenttype",
	"_user_tags",
	"_comments",
	"_assign",
	"_liked_by",
}


MODE_CONFIG = {
	"Nature of Injury": {
		"type": "tms",
		"fieldname": "nature_of_the_injury",
		"label": _("Nature of Injury"),
	},
	"Type of Damage": {
		"type": "tms",
		"fieldname": "type_of_damage",
		"label": _("Type of Damage"),
	},
	"Body Part": {
		"type": "tms",
		"fieldname": "select_type_of_body_part",
		"label": _("Body Part"),
	},
	"Task": {
		"type": "tms",
		"fieldname": "specify_task",
		"label": _("Task"),
	},
	"Severity": {
		"type": "tms",
		"fieldname": "select_severity",
		"label": _("Severity"),
	},
	"Incident Type": {
		"type": "parent",
		"fieldname": "incident_type",
		"label": _("Incident Type"),
		"target_doctype": "Safety Incident Type",
	},
	"Shift Summary": {
		"type": "derived",
		"fieldname": "shift",
		"label": _("Shift"),
		"fixed_values": SHIFT_ORDER,
	},
	"Day of Week": {
		"type": "derived",
		"fieldname": "day_of_week",
		"label": _("Day of Week"),
		"fixed_values": DOW_ORDER,
	},
	"Day of Month": {
		"type": "derived",
		"fieldname": "day_of_month",
		"label": _("Day of Month"),
		"fixed_values": [str(i) for i in range(1, 32)],
	},
	"Hour of Day": {
		"type": "derived",
		"fieldname": "hour_of_day",
		"label": _("Hour of Day"),
		"fixed_values": [f"{i:02d}:00" for i in range(24)],
	},
}


def execute(filters=None):
	filters = filters or {}
	filters = normalize_filters(filters)

	mode = filters["report_mode"]
	layout = filters["layout"]

	parent_rows = get_parent_rows(filters)
	parent_names = {row["name"] for row in parent_rows}

	if not parent_names:
		columns = get_columns(mode, layout, filters)
		return columns, [], None, {}, get_report_summary([], 0)

	parent_names = apply_specialist_filters(parent_names, filters)

	if not parent_names:
		columns = get_columns(mode, layout, filters)
		return columns, [], None, {}, get_report_summary([], 0)

	parent_rows = [row for row in parent_rows if row["name"] in parent_names]

	columns = get_columns(mode, layout, filters)
	data = get_data(mode, layout, filters, parent_rows, parent_names)
	chart = get_chart(data, mode)
	report_summary = get_report_summary(data, len(parent_names))

	return columns, data, None, chart, report_summary


def normalize_filters(filters: dict) -> dict:
	today = date.today()

	if not filters.get("from_date"):
		filters["from_date"] = date(today.year, 1, 1)

	if not filters.get("to_date"):
		filters["to_date"] = date(today.year, 12, 31)

	if not filters.get("report_mode"):
		filters["report_mode"] = "Nature of Injury"

	if not filters.get("layout"):
		filters["layout"] = "Summary"

	from_date = getdate(filters["from_date"])
	to_date = getdate(filters["to_date"])

	if from_date > to_date:
		frappe.throw(_("From Date cannot be after To Date"))

	filters["from_date"] = str(from_date)
	filters["to_date"] = str(to_date)

	return filters


def get_parent_rows(filters: dict) -> list[dict]:
	parent_filters = {
		"datetime_incident": ["between", [filters["from_date"] + " 00:00:00", filters["to_date"] + " 23:59:59"]]
	}

	if filters.get("site"):
		parent_filters["site"] = filters["site"]

	if filters.get("region"):
		parent_filters["region"] = filters["region"]

	if filters.get("departmentx"):
		parent_filters["departmentx"] = filters["departmentx"]

	if filters.get("shift"):
		parent_filters["shift"] = filters["shift"]

	return frappe.get_all(
		"Incident Report",
		filters=parent_filters,
		fields=["name", "datetime_incident", "shift", "incident_type"],
		order_by="datetime_incident asc",
		limit_page_length=0,
	)


def apply_specialist_filters(parent_names: set[str], filters: dict) -> set[str]:
	if not parent_names:
		return set()

	filter_map = [
		("nature_of_injury_filter", "nature_of_the_injury"),
		("type_of_damage_filter", "type_of_damage"),
		("body_part_filter", "select_type_of_body_part"),
		("task_filter", "specify_task"),
		("severity_filter", "select_severity"),
	]

	current = set(parent_names)

	for filter_key, report_fieldname in filter_map:
		if filters.get(filter_key):
			match_names = get_matching_parent_names_for_tms(
				report_fieldname,
				filters[filter_key],
			)
			current &= match_names

	return current


def get_matching_parent_names_for_tms(parent_fieldname: str, selected_value: str) -> set[str]:
	child_doctype, link_fieldname, _target_doctype = get_tms_link_info(parent_fieldname)

	rows = frappe.get_all(
		child_doctype,
		filters={
			"parenttype": "Incident Report",
			link_fieldname: selected_value,
		},
		fields=["parent"],
		limit_page_length=0,
	)

	return {row["parent"] for row in rows}


def get_columns(mode: str, layout: str, filters: dict) -> list[dict]:
	mode_label = MODE_CONFIG[mode]["label"]

	columns = [
		{
			"label": mode_label,
			"fieldname": "label",
			"fieldtype": "Data",
			"width": 260,
		},
		{
			"label": _("Total"),
			"fieldname": "total",
			"fieldtype": "Int",
			"width": 100,
		},
	]

	if layout in ("Yearly", "Matrix"):
		for year in get_years_between(filters["from_date"], filters["to_date"]):
			columns.append(
				{
					"label": str(year),
					"fieldname": f"y{year}",
					"fieldtype": "Int",
					"width": 85,
				}
			)

	if layout in ("Monthly", "Matrix"):
		for month_label, _month_num in MONTHS:
			columns.append(
				{
					"label": _(month_label),
					"fieldname": month_label.lower(),
					"fieldtype": "Int",
					"width": 75,
				}
			)

	return columns


def get_data(mode: str, layout: str, filters: dict, parent_rows: list[dict], parent_names: set[str]) -> list[dict]:
	years = get_years_between(filters["from_date"], filters["to_date"])
	buckets = initialize_bucket_matrix(mode, years)

	mode_type = MODE_CONFIG[mode]["type"]

	if mode_type == "tms":
		accumulate_tms_mode(mode, buckets, years, parent_rows, parent_names)
	elif mode_type == "parent":
		accumulate_parent_mode(mode, buckets, years, parent_rows)
	elif mode_type == "derived":
		accumulate_derived_mode(mode, buckets, years, parent_rows)

	all_labels = get_all_labels_for_mode(mode, buckets)

	data = []
	for label in all_labels:
		row = {"label": label}
		total = 0

		if layout in ("Yearly", "Matrix"):
			for year in years:
				val = int(buckets.get(label, {}).get("years", {}).get(year, 0))
				row[f"y{year}"] = val
				total += val
		else:
			total = sum(int(v or 0) for v in buckets.get(label, {}).get("years", {}).values())

		if layout in ("Monthly", "Matrix"):
			for month_label, month_num in MONTHS:
				row[month_label.lower()] = int(buckets.get(label, {}).get("months", {}).get(month_num, 0))

		row["total"] = total
		data.append(row)

	total_row = {"label": _("Total")}
	grand_total = 0

	if layout in ("Yearly", "Matrix"):
		for year in years:
			s = sum(int(r.get(f"y{year}") or 0) for r in data)
			total_row[f"y{year}"] = s
			grand_total += s
	else:
		grand_total = sum(int(r.get("total") or 0) for r in data)

	if layout in ("Monthly", "Matrix"):
		for month_label, _month_num in MONTHS:
			total_row[month_label.lower()] = sum(int(r.get(month_label.lower()) or 0) for r in data)

	total_row["total"] = grand_total
	data.append(total_row)

	return data


def initialize_bucket_matrix(mode: str, years: list[int]) -> dict[str, dict]:
	labels = get_fixed_labels(mode)

	buckets = {}
	for label in labels:
		buckets[label] = {
			"years": {year: 0 for year in years},
			"months": {m: 0 for _label, m in MONTHS},
		}
	return buckets


def accumulate_tms_mode(mode: str, buckets: dict, years: list[int], parent_rows: list[dict], parent_names: set[str]) -> None:
	parent_map = {row["name"]: row for row in parent_rows}
	parent_fieldname = MODE_CONFIG[mode]["fieldname"]

	child_doctype, link_fieldname, _target_doctype = get_tms_link_info(parent_fieldname)

	rows = frappe.get_all(
		child_doctype,
		filters={
			"parenttype": "Incident Report",
			"parent": ["in", list(parent_names)],
		},
		fields=["parent", link_fieldname],
		order_by="idx asc",
		limit_page_length=0,
	)

	for row in rows:
		parent_name = row["parent"]
		label = row.get(link_fieldname)

		if not label or parent_name not in parent_map:
			continue

		dt = parent_map[parent_name].get("datetime_incident")
		if not dt:
			continue

		yy, mm = extract_year_month(dt)

		if label not in buckets:
			buckets[label] = {
				"years": {year: 0 for year in years},
				"months": {m: 0 for _label, m in MONTHS},
			}

		if yy in buckets[label]["years"]:
			buckets[label]["years"][yy] += 1

		buckets[label]["months"][mm] = buckets[label]["months"].get(mm, 0) + 1


def accumulate_parent_mode(mode: str, buckets: dict, years: list[int], parent_rows: list[dict]) -> None:
	fieldname = MODE_CONFIG[mode]["fieldname"]

	for row in parent_rows:
		label = row.get(fieldname)
		dt = row.get("datetime_incident")

		if not label or not dt:
			continue

		yy, mm = extract_year_month(dt)

		if label not in buckets:
			buckets[label] = {
				"years": {year: 0 for year in years},
				"months": {m: 0 for _label, m in MONTHS},
			}

		if yy in buckets[label]["years"]:
			buckets[label]["years"][yy] += 1

		buckets[label]["months"][mm] = buckets[label]["months"].get(mm, 0) + 1


def accumulate_derived_mode(mode: str, buckets: dict, years: list[int], parent_rows: list[dict]) -> None:
	for row in parent_rows:
		dt = row.get("datetime_incident")
		if not dt:
			continue

		label = derive_bucket_label(mode, row, dt)
		if not label:
			continue

		yy, mm = extract_year_month(dt)

		if label not in buckets:
			buckets[label] = {
				"years": {year: 0 for year in years},
				"months": {m: 0 for _label, m in MONTHS},
			}

		if yy in buckets[label]["years"]:
			buckets[label]["years"][yy] += 1

		buckets[label]["months"][mm] = buckets[label]["months"].get(mm, 0) + 1


def derive_bucket_label(mode: str, row: dict, dt_value) -> str | None:
	dt = to_datetime(dt_value)

	if mode == "Shift Summary":
		return row.get("shift") or None

	if mode == "Day of Week":
		return DOW_ORDER[dt.weekday()]

	if mode == "Day of Month":
		return str(dt.day)

	if mode == "Hour of Day":
		return f"{dt.hour:02d}:00"

	return None


def get_all_labels_for_mode(mode: str, buckets: dict) -> list[str]:
	fixed = get_fixed_labels(mode)
	if fixed:
		return fixed

	mode_type = MODE_CONFIG[mode]["type"]

	if mode_type == "tms":
		parent_fieldname = MODE_CONFIG[mode]["fieldname"]
		_child_doctype, _link_fieldname, target_doctype = get_tms_link_info(parent_fieldname)

		if target_doctype:
			rows = frappe.get_all(target_doctype, fields=["name"], order_by="name asc", limit_page_length=0)
			labels = [r["name"] for r in rows]
			extra = [k for k in buckets.keys() if k not in labels]
			return labels + sorted(extra)

	if mode_type == "parent":
		target_doctype = MODE_CONFIG[mode].get("target_doctype")
		if target_doctype:
			rows = frappe.get_all(target_doctype, fields=["name"], order_by="name asc", limit_page_length=0)
			labels = [r["name"] for r in rows]
			extra = [k for k in buckets.keys() if k not in labels]
			return labels + sorted(extra)

	return sorted(buckets.keys())


def get_fixed_labels(mode: str) -> list[str]:
	return MODE_CONFIG[mode].get("fixed_values", [])


def get_tms_link_info(parent_fieldname: str) -> tuple[str, str, str | None]:
	parent_meta = frappe.get_meta("Incident Report")
	df = parent_meta.get_field(parent_fieldname)

	if not df:
		frappe.throw(_("Field {0} not found on Incident Report").format(parent_fieldname))

	child_doctype = df.options
	child_meta = frappe.get_meta(child_doctype)

	candidate_fields = [
		f for f in child_meta.fields
		if f.fieldname not in SYSTEM_CHILD_FIELDS
		and f.fieldtype in ("Link", "Dynamic Link", "Data", "Select", "Small Text", "Read Only")
	]

	if not candidate_fields:
		frappe.throw(_("Could not determine value field for child table {0}").format(child_doctype))

	link_field = candidate_fields[0]
	target_doctype = link_field.options if link_field.fieldtype == "Link" else None

	return child_doctype, link_field.fieldname, target_doctype


def get_years_between(from_date: str, to_date: str) -> list[int]:
	start = getdate(from_date)
	end = getdate(to_date)
	return list(range(start.year, end.year + 1))


def extract_year_month(dt_value) -> tuple[int, int]:
	dt = to_datetime(dt_value)
	return dt.year, dt.month


def to_datetime(dt_value) -> datetime:
	if isinstance(dt_value, datetime):
		return dt_value

	if isinstance(dt_value, date):
		return datetime(dt_value.year, dt_value.month, dt_value.day)

	return datetime.strptime(str(dt_value), "%Y-%m-%d %H:%M:%S")


def get_chart(data: list[dict], mode: str) -> dict:
	if not data:
		return {}

	rows = [row for row in data if row.get("label") not in ("Total", str(_("Total")))]
	rows = [row for row in rows if int(row.get("total") or 0) > 0]

	if not rows:
		return {}

	rows_sorted = sorted(rows, key=lambda r: int(r.get("total") or 0), reverse=True)[:12]

	return {
		"data": {
			"labels": [row["label"] for row in rows_sorted],
			"datasets": [
				{
					"name": str(MODE_CONFIG[mode]["label"]),
					"values": [int(row.get("total") or 0) for row in rows_sorted],
				}
			],
		},
		"type": "bar",
		"barOptions": {"horizontal": 1, "spaceRatio": 0.35},
		"height": max(320, 28 * len(rows_sorted)),
	}


def get_report_summary(data: list[dict], incident_count: int) -> list[dict]:
	total_row = next((row for row in reversed(data) if row.get("label") in ("Total", str(_("Total")))), None)
	total_counted = int(total_row.get("total") or 0) if total_row else 0

	return [
		{
			"label": _("Incident Records"),
			"value": incident_count,
			"datatype": "Int",
		},
		{
			"label": _("Total Counted"),
			"value": total_counted,
			"datatype": "Int",
		},
	]