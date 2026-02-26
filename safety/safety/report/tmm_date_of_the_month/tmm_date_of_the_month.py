# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import calendar
from datetime import date, datetime

import frappe
from frappe import _


DAY_COLS = list(range(1, 32))  # 1..31


def execute(filters: dict | None = None):
	filters = filters or {}

	columns = get_columns()
	data = get_data(filters)

	chart = get_chart(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns() -> list[dict]:
	cols = [{"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 120}]

	for d in DAY_COLS:
		cols.append(
			{
				"label": str(d),
				"fieldname": f"d{d:02d}",
				"fieldtype": "Data",  # weekday row is text; count row is numeric but Data is ok for both
				"width": 55,
			}
		)

	cols.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 90})
	cols.append({"label": _("Quarter"), "fieldname": "quarter", "fieldtype": "Int", "width": 90})
	return cols


def get_data(filters: dict) -> list[dict]:
	start_date, end_date = _resolve_dates(filters)

	base_conditions = [
		"im.tmm = 1",
		"DATE(im.datetime_incident) BETWEEN %(start_date)s AND %(end_date)s",
	]
	values = {"start_date": start_date, "end_date": end_date}

	if filters.get("site"):
		base_conditions.append("im.site = %(site)s")
		values["site"] = filters["site"]

	where_base = " AND ".join(base_conditions)

	# months in selected range
	month_keys = _month_keys_between(start_date, end_date)  # [(yyyy, mm), ...]

	out: list[dict] = []

	# to build a Year total row like Excel (and also support multi-year ranges)
	years_in_range = sorted({y for y, _m in month_keys})

	for (yy, mm) in month_keys:
		month_start = date(yy, mm, 1)
		last_day = calendar.monthrange(yy, mm)[1]
		month_end = date(yy, mm, last_day)

		# clamp month to filter window
		clamped_start = max(_to_date(start_date), month_start)
		clamped_end = min(_to_date(end_date), month_end)

		# ---- Weekday row (matches Excel: month name + weekday labels across 1..31)
		weekday_row = {"month": calendar.month_abbr[mm]}

		for d in DAY_COLS:
			if d <= last_day:
				weekday = calendar.day_abbr[date(yy, mm, d).weekday()]  # Mon/Tue/...
				weekday_row[f"d{d:02d}"] = weekday
			else:
				weekday_row[f"d{d:02d}"] = ""

		weekday_row["total"] = None

		# Quarter total only on quarter-start months (Jan/Apr/Jul/Oct), like your Excel
		if mm in (1, 4, 7, 10):
			q_total = _get_quarter_total(where_base, values, clamped_start, clamped_end, yy, mm)
			weekday_row["quarter"] = q_total
		else:
			weekday_row["quarter"] = None

		out.append(weekday_row)

		# ---- Count row (matches Excel: blank month cell + counts per day)
		count_row = {"month": ""}

		# fetch counts for this month by day-of-month
		rows = frappe.db.sql(
			f"""
			SELECT
				DAY(im.datetime_incident) AS dom,
				COUNT(*) AS total
			FROM `tabIncident Management` im
			WHERE {where_base}
			  AND DATE(im.datetime_incident) BETWEEN %(m_start)s AND %(m_end)s
			GROUP BY dom
			ORDER BY dom
			""",
			{**values, "m_start": str(clamped_start), "m_end": str(clamped_end)},
			as_dict=True,
		)

		by_day = {int(r["dom"]): int(r["total"] or 0) for r in rows}

		month_total = 0
		for d in DAY_COLS:
			val = by_day.get(d, 0) if d <= last_day else ""
			count_row[f"d{d:02d}"] = val
			if isinstance(val, int):
				month_total += val

		count_row["total"] = month_total
		count_row["quarter"] = None
		out.append(count_row)

	# ---- Year total rows (like "2025" row in your Excel)
	for yy in years_in_range:
		y_start = max(_to_date(start_date), date(yy, 1, 1))
		y_end = min(_to_date(end_date), date(yy, 12, 31))
		if y_start > y_end:
			continue

		rows = frappe.db.sql(
			f"""
			SELECT
				DAY(im.datetime_incident) AS dom,
				COUNT(*) AS total
			FROM `tabIncident Management` im
			WHERE {where_base}
			  AND DATE(im.datetime_incident) BETWEEN %(y_start)s AND %(y_end)s
			GROUP BY dom
			ORDER BY dom
			""",
			{**values, "y_start": str(y_start), "y_end": str(y_end)},
			as_dict=True,
		)

		by_day = {int(r["dom"]): int(r["total"] or 0) for r in rows}

		year_row = {"month": str(yy)}
		year_total = 0
		for d in DAY_COLS:
			val = by_day.get(d, 0)
			year_row[f"d{d:02d}"] = val
			year_total += val

		year_row["total"] = year_total
		year_row["quarter"] = year_total  # matches your Excel behavior (year row quarter == total)
		out.append(year_row)

	# If range spans multiple years, also add a final grand Total row
	if len(years_in_range) > 1:
		grand = {"month": _("Total")}
		grand_total = 0
		for d in DAY_COLS:
			s = 0
			for r in out:
				if r.get("month") and r["month"].isdigit():  # only year rows
					s += int(r.get(f"d{d:02d}") or 0)
			grand[f"d{d:02d}"] = s
			grand_total += s
		grand["total"] = grand_total
		grand["quarter"] = grand_total
		out.append(grand)

	return out


def get_chart(data: list[dict]) -> dict:
	"""
	Chart: totals per day-of-month across the whole filtered range, plus a Total bar.
	We pull totals from the year row if single-year, or the final Total row if multi-year.
	"""
	if not data:
		return {}

	# Find the bottom-most grand summary row:
	# - if multi-year: last row is "Total"
	# - if single-year: last row is that year (e.g. "2025")
	summary_row = None
	for r in reversed(data):
		month = str(r.get("month") or "")
		if month == "Total" or month == str(_("Total")) or month.isdigit():
			summary_row = r
			break

	if not summary_row:
		return {}

	labels = [str(d) for d in DAY_COLS] + ["Total"]
	values = [int(summary_row.get(f"d{d:02d}") or 0) for d in DAY_COLS] + [int(summary_row.get("total") or 0)]

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

	# prefer the same summary row logic as chart
	for r in reversed(data):
		month = str(r.get("month") or "")
		if month == "Total" or month == str(_("Total")) or month.isdigit():
			return [{"label": _("Total TMM Incidents"), "value": int(r.get("total") or 0), "datatype": "Int"}]

	return [{"label": _("Total TMM Incidents"), "value": 0, "datatype": "Int"}]


def _get_quarter_total(where_base: str, values: dict, clamped_start: date, clamped_end: date, yy: int, mm: int) -> int:
	"""
	Quarter total shown only on quarter-start months (Jan/Apr/Jul/Oct).
	We compute the quarter window, clamp it to the filter range, then count.
	"""
	# Determine quarter start/end for the given quarter-start month
	q_start_month = mm
	q_end_month = mm + 2

	q_start = date(yy, q_start_month, 1)
	q_end_last_day = calendar.monthrange(yy, q_end_month)[1]
	q_end = date(yy, q_end_month, q_end_last_day)

	# Clamp quarter to the overall filter window (using the already-clamped month edges helps too)
	overall_start = _to_date(values["start_date"])
	overall_end = _to_date(values["end_date"])

	q_start = max(q_start, overall_start)
	q_end = min(q_end, overall_end)

	if q_start > q_end:
		return 0

	total = frappe.db.sql(
		f"""
		SELECT COUNT(*)
		FROM `tabIncident Management` im
		WHERE {where_base}
		  AND DATE(im.datetime_incident) BETWEEN %(q_start)s AND %(q_end)s
		""",
		{**values, "q_start": str(q_start), "q_end": str(q_end)},
	)[0][0]

	return int(total or 0)


def _resolve_dates(filters: dict) -> tuple[str, str]:
	"""
	Returns (start_date, end_date) as YYYY-MM-DD strings.
	Default: current calendar year.
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