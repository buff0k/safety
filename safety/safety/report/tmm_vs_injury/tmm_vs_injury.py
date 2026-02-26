from __future__ import annotations

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
	cols = [
		{"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 90},
		{"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 70},
	]

	for d in DAY_COLS:
		cols.append(
			{
				"label": str(d),
				"fieldname": f"d{d:02d}",
				"fieldtype": "Data",  # weekday row is text; count rows are ints
				"width": 45,
			}
		)

	cols.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 70})
	return cols


def get_data(filters: dict) -> list[dict]:
	start_date, end_date = _resolve_dates(filters)
	start_dt = _to_date(start_date)
	end_dt = _to_date(end_date)

	# Which years do we show? (like your sheet: show each year present in range)
	years = list(range(start_dt.year, end_dt.year + 1))

	# One query for both series (TMM + Injury)
	conditions = [
		"DATE(im.datetime_incident) BETWEEN %(start_date)s AND %(end_date)s",
	]
	values = {"start_date": start_date, "end_date": end_date}

	if filters.get("site"):
		conditions.append("im.site = %(site)s")
		values["site"] = filters["site"]

	where_clause = " AND ".join(conditions)

	rows = frappe.db.sql(
		f"""
		SELECT
			YEAR(im.datetime_incident) AS yy,
			MONTH(im.datetime_incident) AS mm,
			DAY(im.datetime_incident) AS dd,
			SUM(CASE WHEN im.tmm = 1 THEN 1 ELSE 0 END) AS tmm_cnt,
			SUM(CASE WHEN im.incident_type = 'Injury' THEN 1 ELSE 0 END) AS inj_cnt
		FROM `tabIncident Management` im
		WHERE {where_clause}
		GROUP BY yy, mm, dd
		ORDER BY yy, mm, dd
		""",
		values=values,
		as_dict=True,
	)

	# Build matrices: (yy, mm) -> day -> count
	tmm = {}
	inj = {}
	for r in rows:
		key = (int(r["yy"]), int(r["mm"]))
		dd = int(r["dd"])
		tmm.setdefault(key, {})
		inj.setdefault(key, {})
		tmm[key][dd] = int(r.get("tmm_cnt") or 0)
		inj[key][dd] = int(r.get("inj_cnt") or 0)

	out: list[dict] = []

	# For each year, show Jan..Dec (same as Excel format), even if zeros
	for yy in years:
		for mm in range(1, 13):
			# Month weekday row
			out.append(_weekday_row(yy, mm))

			# TMM row
			out.append(_count_row(calendar.month_abbr[mm], "TMM", yy, mm, tmm.get((yy, mm), {})))

			# Injury row
			out.append(_count_row("", "Injury", yy, mm, inj.get((yy, mm), {})))

		# Year totals (two rows: TMM + Injury)
		out.append(_year_total_row(yy, "TMM", tmm, start_dt, end_dt))
		out.append(_year_total_row(yy, "Injury", inj, start_dt, end_dt))

	# Grand totals at bottom (two rows like your sheet)
	out.append(_grand_total_row("Total", "TMM", out))
	out.append(_grand_total_row("Total", "Injury", out))

	return out


def _weekday_row(yy: int, mm: int) -> dict:
	"""
	Row that shows weekday abbreviations under each day number (Sun/Mon/Tue...),
	blank for invalid days (e.g., 31 in Feb).
	"""
	last_day = calendar.monthrange(yy, mm)[1]
	row = {"month": calendar.month_abbr[mm], "type": ""}

	for d in DAY_COLS:
		if d <= last_day:
			wd = calendar.day_abbr[date(yy, mm, d).weekday()]  # Mon/Tue/...
			row[f"d{d:02d}"] = wd
		else:
			row[f"d{d:02d}"] = ""

	row["total"] = None
	return row


def _count_row(month_label: str, type_label: str, yy: int, mm: int, day_counts: dict[int, int]) -> dict:
	last_day = calendar.monthrange(yy, mm)[1]

	row = {"month": month_label, "type": type_label}
	total = 0

	for d in DAY_COLS:
		if d <= last_day:
			val = int(day_counts.get(d, 0))
			row[f"d{d:02d}"] = val
			total += val
		else:
			row[f"d{d:02d}"] = ""
	row["total"] = total
	return row


def _year_total_row(
	yy: int,
	type_label: str,
	matrix: dict[tuple[int, int], dict[int, int]],
	start_dt: date,
	end_dt: date,
) -> dict:
	"""
	Matches your sheet: a row labelled with the year in Month column,
	Type = TMM/Injury, and totals by day-of-month across the whole year (within filter range).
	"""
	row = {"month": str(yy), "type": type_label}

	# Clamp to filter window
	y_start = max(start_dt, date(yy, 1, 1))
	y_end = min(end_dt, date(yy, 12, 31))
	if y_start > y_end:
		for d in DAY_COLS:
			row[f"d{d:02d}"] = 0
		row["total"] = 0
		return row

	total = 0
	for d in DAY_COLS:
		s = 0
		# Sum across all months in the year for that day-of-month
		for mm in range(1, 13):
			# only count days that exist in that month
			last_day = calendar.monthrange(yy, mm)[1]
			if d <= last_day:
				# also enforce filter clamp for partial years
				current_date = date(yy, mm, d)
				if y_start <= current_date <= y_end:
					s += int(matrix.get((yy, mm), {}).get(d, 0))
		row[f"d{d:02d}"] = s
		total += s

	row["total"] = total
	return row


def _grand_total_row(label_month: str, type_label: str, rows: list[dict]) -> dict:
	"""
	Bottom totals row:
	Month = "Total", Type = "TMM"/"Injury", sums the YEAR rows.
	"""
	row = {"month": label_month, "type": type_label}
	total = 0

	# sum only year rows for that type
	year_rows = [r for r in rows if str(r.get("month", "")).isdigit() and r.get("type") == type_label]

	for d in DAY_COLS:
		s = sum(int(r.get(f"d{d:02d}") or 0) for r in year_rows)
		row[f"d{d:02d}"] = s
		total += s

	row["total"] = total
	return row


def get_chart(data: list[dict]) -> dict:
	"""
	Simple chart: totals per day-of-month for TMM and Injury (from the bottom Total rows) + Total bar.
	"""
	if not data:
		return {}

	tmm_total = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "TMM"), None)
	inj_total = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "Injury"), None)
	if not tmm_total or not inj_total:
		return {}

	labels = [str(d) for d in DAY_COLS] + ["Total"]
	tmm_vals = [int(tmm_total.get(f"d{d:02d}") or 0) for d in DAY_COLS] + [int(tmm_total.get("total") or 0)]
	inj_vals = [int(inj_total.get(f"d{d:02d}") or 0) for d in DAY_COLS] + [int(inj_total.get("total") or 0)]

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("TMM"), "values": tmm_vals},
				{"name": _("Injury"), "values": inj_vals},
			],
		},
		"type": "bar",
	}


def get_report_summary(data: list[dict]) -> list[dict]:
	if not data:
		return [{"label": _("Grand Total"), "value": 0, "datatype": "Int"}]

	tmm_total = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "TMM"), None)
	inj_total = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "Injury"), None)

	total = int(tmm_total.get("total") or 0) + int(inj_total.get("total") or 0) if (tmm_total and inj_total) else 0
	return [{"label": _("Grand Total (TMM + Injury)"), "value": total, "datatype": "Int"}]


def _resolve_dates(filters: dict) -> tuple[str, str]:
	s = filters.get("start_date")
	e = filters.get("end_date")

	if s and e:
		return str(s), str(e)

	today = date.today()
	return str(s or date(today.year, 1, 1)), str(e or date(today.year, 12, 31))


def _to_date(d: str | date) -> date:
	if isinstance(d, date):
		return d
	try:
		return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
	except Exception:
		return frappe.utils.getdate(d)