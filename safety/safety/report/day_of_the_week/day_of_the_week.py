# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import calendar
from datetime import date, datetime

import frappe
from frappe import _


DOW_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def execute(filters: dict | None = None):
	filters = filters or {}

	columns = get_columns()
	data = get_data(filters)

	chart = get_chart(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns() -> list[dict]:
	cols = [
		{"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 120},
	]
	for d in DOW_ORDER:
		cols.append({"label": _(d), "fieldname": d.lower(), "fieldtype": "Int", "width": 80})
	cols.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 100})
	return cols


def get_data(filters: dict) -> list[dict]:
	start_date, end_date = _resolve_dates(filters)

	conditions = ["im.tmm = 1", "DATE(im.datetime_incident) BETWEEN %(start_date)s AND %(end_date)s"]
	values = {"start_date": start_date, "end_date": end_date}

	if filters.get("site"):
		conditions.append("im.site = %(site)s")
		values["site"] = filters["site"]

	where_clause = " AND ".join(conditions)

	# Months in selected date range
	month_keys = _month_keys_between(start_date, end_date)  # list of (year, month)
	month_label_map = {(y, m): calendar.month_abbr[m] for (y, m) in month_keys}

	# Initialise matrix
	matrix = {(y, m): {d: 0 for d in DOW_ORDER} for (y, m) in month_keys}

	# WEEKDAY(): 0=Mon ... 6=Sun
	rows = frappe.db.sql(
		f"""
		SELECT
			YEAR(im.datetime_incident) AS yy,
			MONTH(im.datetime_incident) AS mm,
			WEEKDAY(im.datetime_incident) AS wd,
			COUNT(*) AS total
		FROM `tabIncident Management` im
		WHERE {where_clause}
		GROUP BY yy, mm, wd
		ORDER BY yy, mm, wd
		""",
		values=values,
		as_dict=True,
	)

	for r in rows:
		key = (int(r["yy"]), int(r["mm"]))
		if key not in matrix:
			continue
		dow = DOW_ORDER[int(r["wd"])]
		matrix[key][dow] = int(r["total"] or 0)

	# Build output rows
	out: list[dict] = []
	for (y, m) in month_keys:
		row = {"month": month_label_map[(y, m)]}
		row_total = 0
		for d in DOW_ORDER:
			val = int(matrix[(y, m)].get(d, 0))
			row[d.lower()] = val
			row_total += val
		row["total"] = row_total
		out.append(row)

	# Bottom Total row
	total_row = {"month": _("Total")}
	grand_total = 0
	for d in DOW_ORDER:
		s = sum(int(r[d.lower()]) for r in out) if out else 0
		total_row[d.lower()] = s
		grand_total += s
	total_row["total"] = grand_total
	out.append(total_row)

	return out


def get_chart(data: list[dict]) -> dict:
	if not data:
		return {}

	# Use the bottom total row
	total_row = data[-1] if str(data[-1].get("month")) in ("Total", str(_("Total"))) else None
	if not total_row:
		return {}

	# Add "Total" as an extra bar at the end
	labels = DOW_ORDER + ["Total"]
	values = [int(total_row.get(d.lower()) or 0) for d in DOW_ORDER] + [int(total_row.get("total") or 0)]

	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("TMM Incidents"), "values": values}],
		},
		"type": "bar",
	}


def get_report_summary(data: list[dict]) -> list[dict]:
	if not data:
		return [{"label": _("Total TMM Incidents"), "value": 0, "datatype": "Int"}]

	total_row = data[-1]
	total = int(total_row.get("total") or 0)
	return [{"label": _("Total TMM Incidents"), "value": total, "datatype": "Int"}]


def _resolve_dates(filters: dict) -> tuple[str, str]:
	"""
	Returns (start_date, end_date) as YYYY-MM-DD strings.

	If user does not provide dates:
	- default is current calendar year (Jan 1 -> Dec 31)
	"""
	s = filters.get("start_date")
	e = filters.get("end_date")

	if s and e:
		return str(s), str(e)

	today = date.today()
	default_start = date(today.year, 1, 1)
	default_end = date(today.year, 12, 31)

	return str(s or default_start), str(e or default_end)


def _month_keys_between(start_date_str: str, end_date_str: str) -> list[tuple[int, int]]:
	start = _to_date(start_date_str)
	end = _to_date(end_date_str)

	keys: list[tuple[int, int]] = []
	y, m = start.year, start.month
	while (y, m) <= (end.year, end.month):
		keys.append((y, m))
		if m == 12:
			y += 1
			m = 1
		else:
			m += 1
	return keys


def _to_date(d: str | date) -> date:
	if isinstance(d, date):
		return d
	try:
		return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
	except Exception:
		return frappe.utils.getdate(d)