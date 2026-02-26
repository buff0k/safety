from __future__ import annotations

from datetime import date, datetime

import frappe
from frappe import _

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

# Spreadsheet label -> DocType checkbox fieldname
TASKS = [
	("Maintenance of equipment", "maintenance_of_equipment"),
	("Repairing equipment", "repairing_equipment"),
	("Assembling equipment", "assembling_equipment"),
	("Installation and erection of equipment e.g. pipes, winches", "installation_erection_of_equipment"),
	("Construction/building permanent structure e.g. concrete, steelwork", "construction_building"),
	("Manufacturing e.g. sheet metal, carpentry", "manufacturing"),
	("Lifting e.g. cranes, block and tackle, chainblock", "lifting"),
	("Digging, drilling, dredging", "dig_drill_dredge"),
	("Drilling", "drilling"),  # ✅ now supported by your DocType
	("Preparing the face", "preparing_the_face"),
	("Charging", "charging"),
	("Blasting", "blasting"),
	("Transporting of mineral/rock/ore by", "transport_rock_mineral_ore"),
	("Transporting of people by", "transporting_of_people_by"),
	("Transporting of materials/equipment by", "transport_material_equipment_by"),
	("Material handling (loading, unloading, stacking)", "material_handling"),
	("General maintenance/housekeeping", "maintenance_housekeeping"),
	# Optional if you want:
	# ("Other", "oth"),
]


def execute(filters: dict | None = None):
	filters = filters or {}

	start_date, end_date = _resolve_dates(filters)
	year_cols = _years_between(start_date, end_date)

	columns = get_columns(year_cols)
	data = get_data(filters, start_date, end_date, year_cols)

	chart = get_chart(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns(year_cols: list[int]) -> list[dict]:
	cols = [
		{"label": _("TASK: PERSON INJURED WHILE PERFORMING"), "fieldname": "task", "fieldtype": "Data", "width": 360},
		{"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 80},
	]

	for y in year_cols:
		cols.append({"label": str(y), "fieldname": f"y{y}", "fieldtype": "Int", "width": 70})

	for m_label, _m_num in MONTHS:
		cols.append({"label": _(m_label), "fieldname": m_label.lower(), "fieldtype": "Int", "width": 70})

	return cols


def get_data(filters: dict, start_date: str, end_date: str, year_cols: list[int]) -> list[dict]:
	# injuries only
	conditions_base = [
		"im.incident_type = 'Injury'",
		"DATE(im.datetime_incident) BETWEEN %(start_date)s AND %(end_date)s",
	]
	values = {"start_date": start_date, "end_date": end_date}

	if filters.get("site"):
		conditions_base.append("im.site = %(site)s")
		values["site"] = filters["site"]

	where_base = " AND ".join(conditions_base)

	matrix: dict[str, dict[str, dict[int, int]]] = {}  # label -> {"years":{}, "months":{}}

	for label, fieldname in TASKS:
		matrix[label] = {"years": {y: 0 for y in year_cols}, "months": {m: 0 for _ml, m in MONTHS}}

		rows = frappe.db.sql(
			f"""
			SELECT
				YEAR(im.datetime_incident) AS yy,
				MONTH(im.datetime_incident) AS mm,
				COUNT(*) AS total
			FROM `tabIncident Management` im
			WHERE {where_base}
			  AND IFNULL(im.`{fieldname}`, 0) = 1
			GROUP BY yy, mm
			""",
			values=values,
			as_dict=True,
		)

		for r in rows:
			yy = int(r["yy"])
			mm = int(r["mm"])
			cnt = int(r["total"] or 0)

			if yy in matrix[label]["years"]:
				matrix[label]["years"][yy] += cnt
			matrix[label]["months"][mm] = matrix[label]["months"].get(mm, 0) + cnt

	out: list[dict] = []
	for label, _fieldname in TASKS:
		row = {"task": label}
		total = 0

		for y in year_cols:
			val = int(matrix[label]["years"].get(y, 0))
			row[f"y{y}"] = val
			total += val

		for m_label, m_num in MONTHS:
			row[m_label.lower()] = int(matrix[label]["months"].get(m_num, 0))

		row["total"] = total
		out.append(row)

	# Bottom Total Injuries row (sum of all tasks)
	total_row = {"task": _("Total Injuries")}
	grand_total = 0

	for y in year_cols:
		s = sum(int(r.get(f"y{y}") or 0) for r in out)
		total_row[f"y{y}"] = s
		grand_total += s

	for m_label, _m_num in MONTHS:
		total_row[m_label.lower()] = sum(int(r.get(m_label.lower()) or 0) for r in out)

	total_row["total"] = grand_total
	out.append(total_row)

	return out


def get_chart(data: list[dict]) -> dict:
	"""
	Horizontal bar chart:
	Total Injuries first, then tasks sorted by Total desc.
	"""
	if not data:
		return {}

	total_row = data[-1] if "Total Injuries" in str(data[-1].get("task")) else None
	grand_total = int(total_row.get("total") or 0) if total_row else 0

	rows = [r for r in data if "Total Injuries" not in str(r.get("task"))]
	rows_sorted = sorted(rows, key=lambda r: int(r.get("total") or 0), reverse=True)

	labels = ["Total Injuries"] + [r["task"] for r in rows_sorted]
	values = [grand_total] + [int(r.get("total") or 0) for r in rows_sorted]

	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Total"), "values": values}],
		},
		"type": "bar",
		"barOptions": {"horizontal": 1, "spaceRatio": 0.5},
		"height": max(500, 26 * len(labels)),
	}


def get_report_summary(data: list[dict]) -> list[dict]:
	if not data:
		return [{"label": _("Total Injuries"), "value": 0, "datatype": "Int"}]

	last = data[-1]
	total = int(last.get("total") or 0) if "Total Injuries" in str(last.get("task")) else 0
	return [{"label": _("Total Injuries"), "value": total, "datatype": "Int"}]


def _resolve_dates(filters: dict) -> tuple[str, str]:
	s = filters.get("start_date")
	e = filters.get("end_date")

	if s and e:
		return str(s), str(e)

	today = date.today()
	return str(s or date(today.year, 1, 1)), str(e or date(today.year, 12, 31))


def _years_between(start_date_str: str, end_date_str: str) -> list[int]:
	start = _to_date(start_date_str)
	end = _to_date(end_date_str)
	return list(range(start.year, end.year + 1))


def _to_date(d: str | date) -> date:
	if isinstance(d, date):
		return d
	try:
		return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
	except Exception:
		return frappe.utils.getdate(d)